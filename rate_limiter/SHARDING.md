# Redis Sharding Strategy for 1 Billion Users

## Problem

Each user has one rate-limit key (`rl:{user_id}`) containing two small
fields (~80 bytes).  At 1B users the worst-case working set is:

    1,000,000,000 × 80 B ≈ 80 GB

A single Redis instance maxes out at ~25 GB usable.  We need to
**horizontally shard** across multiple Redis nodes.

---

## Solution: Redis Cluster (CRC16 Hash Slots)

Redis Cluster partitions the keyspace into **16 384 hash slots**.  Each
key is assigned to a slot via:

    slot = CRC16(key) mod 16384

Our key format `rl:{user_id}` (where `user_id` is a UUID or numeric ID)
distributes uniformly across all slots because UUIDs / numeric IDs have
high entropy.

### Topology

| Users         | Memory     | Nodes (primary) | Replicas | Total  |
|---------------|-----------|-----------------|----------|--------|
| 100 M         | ~8 GB     | 3               | 3        | 6      |
| 500 M         | ~40 GB    | 8               | 8        | 16     |
| 1 B           | ~80 GB    | 16              | 16       | 32     |
| 1 B (headroom)| ~80 GB    | 20              | 20       | 40     |

Each primary handles ~1 024 slots (16 384 / 16) ≈ 62.5 M keys ≈ 5 GB.

### Why NOT Hash Tags

Redis hash tags (`{tag}`) force keys to the same slot.  Example:

    rl:{shard_001}:user_abc → slot = CRC16("shard_001")

This is useful when you need multi-key atomicity (e.g., transactions),
but our Lua script operates on **a single key** per call.  Hash tags
would create **hot spots** and defeat the purpose of sharding.

**Rule:** Do NOT use `{}` hash tags in rate-limit keys.

---

## Atomic Lua Scripts in a Cluster

The Lua script touches exactly **one key** (`KEYS[1]`), so Redis Cluster
routes it to the correct shard automatically.  No cross-slot operations,
no `CROSSSLOT` errors.

---

## Memory Optimization at Scale

| Technique                | Savings                                    |
|--------------------------|--------------------------------------------|
| **Key TTL / auto-expire**| Dormant keys (inactive users) are pruned   |
| **Short key prefix**     | `rl:` (3 bytes) instead of `rate_limit:`   |
| **Integer user IDs**     | 8 bytes vs 36 bytes for UUID strings       |
| **Hash encoding**        | Redis ziplist for small hashes (< 128 B)   |

Our Lua script sets `EXPIRE` on every write:

    TTL = max(60, 2 × bucket_size / refill_rate)

At default settings (100 tokens, 10/s refill) → TTL = 20 s → clamped
to 60 s.  A user inactive for 60 s has their key evicted, freeing memory.

At 1 B total users, if only 10% are active in any 60 s window, the live
key count is ~100 M → ~8 GB across the cluster.

---

## Client Configuration

```python
# Production: Redis Cluster client
import redis
rc = redis.RedisCluster(
    startup_nodes=[
        {"host": "redis-1.swift.ai", "port": 6379},
        {"host": "redis-2.swift.ai", "port": 6379},
        {"host": "redis-3.swift.ai", "port": 6379},
    ],
    decode_responses=True,
    skip_full_coverage_check=True,
)

limiter = TokenBucketLimiter(
    bucket_size=100,
    refill_rate=10.0,
    redis_client=rc,        # Cluster-aware client
)
```

The `redis-py` cluster client automatically:
1. Discovers all shards via `CLUSTER SLOTS`
2. Routes each EVALSHA to the correct shard based on `KEYS[1]`
3. Follows `MOVED` / `ASK` redirections during resharding

---

## Capacity Planning Formula

```
nodes = ceil(active_users × 80 B / memory_per_node)
```

Where `memory_per_node` is typically 5–8 GB to leave headroom for
Redis overhead, replication buffers, and Lua script execution memory.

---

## Monitoring

Track these Redis metrics per shard:

| Metric                    | Alert Threshold |
|---------------------------|-----------------|
| `used_memory`             | > 80% of max    |
| `connected_clients`       | > 10 000        |
| `instantaneous_ops_per_sec`| > 100 000      |
| `keyspace_hits / misses`  | miss rate > 5%  |
| `expired_keys`            | trending up OK  |
