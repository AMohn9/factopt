-- factopt headless throughput-measurement scenario.
--
-- The Python harness (factopt.sim.harness) writes `job.lua` next to this file
-- with the blueprint string, input sources, output item, run length, and speed.
-- This scenario builds the block, feeds its inputs from infinity chests, powers
-- it from an electric-energy-interface, runs it at high speed, then writes the
-- measured output rate to `script-output/factopt_sim_result.json`.
--
-- NOTE: entity facing for the source inserters and the exact statistics API can
-- vary by Factorio version; verify in-game on first use (see the marked spots).

local job = require("job")

local RESULT_FILE = "factopt_sim_result.json"
local D = defines.direction

local state = { measured = false }

local function force_and_surface()
  local force = game.forces.player
  local surface = game.surfaces[1]
  return force, surface
end

-- Lay a solid buildable floor over a generous area so terrain never blocks the
-- build, then clear anything already there.
local function prepare_ground(surface)
  local R = 220
  local tiles = {}
  for x = -20, R do
    for y = -20, R do
      tiles[#tiles + 1] = { name = "refined-concrete", position = { x, y } }
    end
  end
  surface.set_tiles(tiles, true)
  for _, e in pairs(surface.find_entities_filtered{ area = {{-20, -20}, {R, R}} }) do
    if e.type ~= "character" then e.destroy() end
  end
end

local function build_block(force, surface)
  local inv = game.create_inventory(1)
  inv.insert{ name = "blueprint" }
  local bp = inv[1]
  bp.import_stack(job.blueprint)
  local ghosts = bp.build_blueprint{
    surface = surface,
    force = force,
    position = { x = 0, y = 0 },
    force_build = true,
  }
  for _, g in pairs(ghosts) do
    if g.valid and g.name == "entity-ghost" then
      g.revive()
    end
  end
end

local function add_infinite_power(force, surface)
  local eei = surface.create_entity{
    name = "electric-energy-interface",
    position = { x = -5.5, y = -5.5 },
    force = force,
  }
  if eei then
    pcall(function()
      eei.power_production = "10000GW"
      eei.electric_buffer_size = 1e18
      eei.energy = 1e18
    end)
  end
end

-- For each source, keep the input belt saturated: an infinity chest (full of the
-- item) two tiles upstream, and a filter inserter one tile upstream dropping onto
-- the belt tile at (s.x, s.y).
local function wire_sources(force, surface)
  for _, s in pairs(job.sources) do
    local stack = game.item_prototypes and game.item_prototypes[s.item]
      and game.item_prototypes[s.item].stack_size or 100
    local chest = surface.create_entity{
      name = "infinity-chest",
      position = { x = s.x - 2 + 0.5, y = s.y + 0.5 },
      force = force,
    }
    if chest then
      pcall(function()
        chest.set_infinity_container_filter(1, {
          name = s.item, count = stack, mode = "at-least", index = 1,
        })
        chest.remove_unfiltered_items = true
      end)
    end
    local ins = surface.create_entity{
      name = "fast-inserter",
      position = { x = s.x - 1 + 0.5, y = s.y + 0.5 },
      force = force,
      direction = D.east,  -- pick from the chest (west), drop onto the belt (east)
    }
    if ins then
      pcall(function()
        ins.inserter_filter_mode = "whitelist"
        ins.set_filter(1, s.item)
      end)
    end
  end
end

local function output_per_sec(force, surface)
  -- Trailing one-minute production window / 60 == items/sec. Handles the 2.0
  -- (get_item_production_statistics/category) and 1.1 (item_production_statistics/
  -- input) shapes.
  local ok, stats = pcall(function()
    return force.get_item_production_statistics(surface)
  end)
  if not ok or not stats then
    stats = force.item_production_statistics
  end
  local made = 0
  local ok2 = pcall(function()
    made = stats.get_flow_count{
      name = job.output, category = "output",
      precision = defines.flow_precision_index.one_minute, count = true,
    }
  end)
  if not ok2 then
    made = stats.get_flow_count{
      name = job.output, input = true,
      precision = defines.flow_precision_index.one_minute, count = true,
    }
  end
  return made / 60.0
end

script.on_init(function()
  local force, surface = force_and_surface()
  game.speed = job.speed
  prepare_ground(surface)
  build_block(force, surface)
  add_infinite_power(force, surface)
  wire_sources(force, surface)
end)

script.on_event(defines.events.on_tick, function(event)
  if state.measured or event.tick < job.ticks then
    return
  end
  state.measured = true
  local force, surface = force_and_surface()
  local rate = output_per_sec(force, surface)
  game.write_file(RESULT_FILE, game.table_to_json({
    done = true,
    output_item = job.output,
    output_per_sec = rate,
    ticks = event.tick,
  }), false)
end)
