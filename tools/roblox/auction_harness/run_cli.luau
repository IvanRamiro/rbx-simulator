-- Runs the Auction House's transaction tests with the Luau CLI, from the project root:
--   luau tools/roblox/auction_harness/run_cli.luau
local Core = require("../../../src/server/Auction/AuctionCore")
local run = require("./AuctionHarness")
local passed, failed = run(Core, print)
if failed > 0 then
    error(failed .. " checks failed")
end
