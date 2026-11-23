-- A very small test kit: t.test(name, fn) runs fn under pcall; t.eq, t.near, t.ok, t.falsy, t.throws assert; t.finish() prints the summary and
-- fails the process when anything failed (so `tests/run.py` and CI see it).
local t = {}

local passed, failed = 0, 0
local failures = {}

function t.test(name, fn)
    local ok, err = pcall(fn)
    if ok then
        passed += 1
    else
        failed += 1
        table.insert(failures, string.format("  FAIL %s\n       %s", name, tostring(err)))
    end
end

function t.eq(actual, expected, message)
    if actual ~= expected then
        error(string.format("%s: expected %s, got %s", message or "values differ", tostring(expected), tostring(actual)), 2)
    end
end

function t.near(actual, expected, epsilon, message)
    if type(actual) ~= "number" or math.abs(actual - expected) > (epsilon or 1e-9) then
        error(string.format("%s: expected %s (+-%s), got %s", message or "numbers differ", tostring(expected), tostring(epsilon or 1e-9), tostring(actual)), 2)
    end
end

function t.ok(value, message)
    if not value then
        error(message or "expected a truthy value", 2)
    end
end

function t.falsy(value, message)
    if value then
        error(message or "expected a falsy value", 2)
    end
end

function t.throws(fn, message)
    if pcall(fn) then
        error(message or "expected an error", 2)
    end
end

function t.finish(name)
    for _, line in failures do
        print(line)
    end
    print(string.format("%s: %d passed, %d failed", name, passed, failed))
    if failed > 0 then
        error("tests failed", 0)
    end
end

return t
