-- ──────────────────────────────────────────────────────────────────
-- Distributed Token Bucket Rate Limiter (Atomic Lua Script)
-- ──────────────────────────────────────────────────────────────────
-- Runs as a single atomic EVALSHA call — one Redis round-trip,
-- no race conditions, no distributed locks needed.
--
-- KEYS[1]  = rate-limit key  e.g. "rl:{user_id}"
-- ARGV[1]  = bucket_size     max tokens (burst capacity)
-- ARGV[2]  = refill_rate     tokens added per second
-- ARGV[3]  = now             current time (seconds, float)
-- ARGV[4]  = requested       tokens to consume (usually 1)
--
-- Returns: { allowed (0|1), current_tokens, retry_after_seconds }
-- ──────────────────────────────────────────────────────────────────

local key           = KEYS[1]
local bucket_size   = tonumber(ARGV[1])
local refill_rate   = tonumber(ARGV[2])
local now           = tonumber(ARGV[3])
local requested     = tonumber(ARGV[4])

-- ── Fetch current state ──────────────────────────────────────────
local data           = redis.call('HMGET', key, 'tokens', 'last_refreshed')
local tokens         = tonumber(data[1])
local last_refreshed = tonumber(data[2])

-- First request for this key — start with a full bucket
if tokens == nil then
    tokens         = bucket_size
    last_refreshed = now
end

-- ── Refill tokens based on elapsed time ──────────────────────────
local elapsed    = math.max(0, now - last_refreshed)
local new_tokens = elapsed * refill_rate
tokens           = math.min(bucket_size, tokens + new_tokens)

-- ── Consume or reject ────────────────────────────────────────────
local allowed     = 0
local retry_after = 0

if tokens >= requested then
    tokens  = tokens - requested
    allowed = 1
else
    -- Seconds until enough tokens accumulate
    retry_after = (requested - tokens) / refill_rate
end

-- ── Persist state ────────────────────────────────────────────────
redis.call('HMSET', key, 'tokens', tostring(tokens), 'last_refreshed', tostring(now))

-- Auto-expire inactive keys: 2× the time to fill a full bucket, min 60s.
-- At 1B users this prevents unbounded memory growth from dormant keys.
local ttl = math.ceil(bucket_size / refill_rate) * 2
if ttl < 60 then ttl = 60 end
redis.call('EXPIRE', key, ttl)

return { allowed, tostring(tokens), tostring(retry_after) }
