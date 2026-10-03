import hashlib
import json
import gdb

EVENTS = r"D:\Prog\simant_recon\build\workers\whole_runtime_flow_review\gdb-events.jsonl"
event_file = open(EVENTS, "w", encoding="utf-8")
inf = gdb.selected_inferior()
sim_calls = 0
map_build_calls = 0
map_row_conversions = 0
bitmap_calls = 0
map_raster_events = 0
active_map_image_pointer = 0
map_image_lock_calls = 0

def emit(kind, **fields):
    event_file.write(json.dumps({"event": kind, **fields}, sort_keys=True) + "\n")
    event_file.flush()

def val(expr):
    return int(gdb.parse_and_eval(expr))

def digest_symbol(symbol, size):
    address = int(gdb.parse_and_eval("&" + symbol))
    return hashlib.sha256(bytes(inf.read_memory(address, size))).hexdigest()

def array_digest(symbol, count):
    if count <= 0:
        return hashlib.sha256(b"").hexdigest()
    address = int(gdb.parse_and_eval("&" + symbol + "[0]"))
    return hashlib.sha256(bytes(inf.read_memory(address, count))).hexdigest()

def sim_snapshot():
    count = val("ListIndexA")
    return {
        "cycle": val("native_state_Cycle.signed_value"),
        "sim_tick": val("native_state_fd_50F6_0C26.unsigned_value"),
        "list_count": count,
        "LifeA": digest_symbol("LifeA", 128 * 64),
        "MapA": digest_symbol("MapA", 128 * 64),
        "AlistX": array_digest("AlistX", count),
        "AlistY": array_digest("AlistY", count),
        "AlistT": array_digest("AlistT", count),
        "AlistM": array_digest("AlistM", count),
    }

def map_buffer_digest():
    try:
        cell = val("fd_50F6_385A")
        address = int(gdb.parse_and_eval("*fd_50F6_385A"))
        if not address:
            return {"handle_cell": cell, "buffer": 0, "sha256_8192": None}
        data = bytes(inf.read_memory(address, 0x2000))
        return {"handle_cell": cell, "buffer": address,
                "sha256_8192": hashlib.sha256(data).hexdigest(),
                "nonzero_bytes": sum(1 for x in data if x),
                "distinct_byte_values": len(set(data))}
    except Exception as e:
        return {"error": str(e)}

class SimReturn(gdb.FinishBreakpoint):
    def __init__(self, before, call_number):
        super().__init__(gdb.newest_frame(), internal=True)
        self.before = before
        self.call_number = call_number
    def stop(self):
        try:
            after = sim_snapshot()
            emit("DoAntSim-return", call=self.call_number, before=self.before, after=after,
                 changed={k: self.before[k] != after[k] for k in self.before})
        except Exception as e:
            emit("DoAntSim-return-error", call=self.call_number, error=str(e))
        return False

class SimEntry(gdb.Breakpoint):
    def __init__(self):
        super().__init__("DoAntSim", internal=True)
    def stop(self):
        global sim_calls
        sim_calls += 1
        try:
            before = sim_snapshot()
            emit("DoAntSim-entry", call=sim_calls, state=before)
            SimReturn(before, sim_calls)
        except Exception as e:
            emit("DoAntSim-entry-error", call=sim_calls, error=str(e))
        return False

class MapBuildReturn(gdb.FinishBreakpoint):
    def __init__(self, before, call_number):
        super().__init__(gdb.newest_frame(), internal=True)
        self.before = before
        self.call_number = call_number
    def stop(self):
        try:
            emit("o12_384C_0432-return", call=self.call_number,
                 mode=val("fd_3D57_07C8"), image_before=self.before,
                 image_after=map_buffer_digest(), row_conversions=map_row_conversions,
                 bitmap_callbacks=bitmap_calls)
        except Exception as e:
            emit("map-build-return-error", call=self.call_number, error=str(e))
        return False

class MapBuildEntry(gdb.Breakpoint):
    def __init__(self):
        super().__init__("o12_384C_0432", internal=True)
    def stop(self):
        global map_build_calls
        map_build_calls += 1
        try:
            life = bytes(inf.read_memory(int(gdb.parse_and_eval("&LifeA[0][0]")), 128 * 64))
            emit("o12_384C_0432-entry", call=map_build_calls,
                 mode=val("fd_3D57_07C8"), image_before=map_buffer_digest(),
                 LifeA_nonzero=sum(1 for x in life if x),
                 MapA_sha256=digest_symbol("MapA", 128 * 64))
            MapBuildReturn(map_buffer_digest(), map_build_calls)
        except Exception as e:
            emit("map-build-entry-error", call=map_build_calls, error=str(e))
        return False

class MapSubsurfaceReturn(gdb.FinishBreakpoint):
    def __init__(self, before, call_number):
        super().__init__(gdb.newest_frame(), internal=True)
        self.before = before
        self.call_number = call_number
    def stop(self):
        try:
            image = {}
            if active_map_image_pointer:
                data = bytes(inf.read_memory(active_map_image_pointer, 0x2000))
                image = {"pointer": active_map_image_pointer,
                         "sha256_8192": hashlib.sha256(data).hexdigest(),
                         "nonzero_bytes": sum(1 for x in data if x),
                         "distinct_byte_values": len(set(data))}
            emit("o12_384C_080E-return", call=self.call_number, mode=val("fd_3D57_07C8"),
                 image_before=self.before["image"], image_after=image,
                 LifeB=self.before["LifeB"], MapB=self.before["MapB"])
        except Exception as e:
            emit("o12_384C_080E-return-error", call=self.call_number, error=str(e))
        return False

class MapSubsurfaceEntry(gdb.Breakpoint):
    def __init__(self):
        super().__init__("o12_384C_080E", internal=True)
        self.count = 0
    def stop(self):
        global active_map_image_pointer
        self.count += 1
        active_map_image_pointer = 0
        try:
            before = {"image": map_buffer_digest(),
                      "LifeB": digest_symbol("LifeB", 64 * 64),
                      "MapB": digest_symbol("MapB", 64 * 64)}
            emit("o12_384C_080E-entry", call=self.count, mode=val("fd_3D57_07C8"),
                 LifeB_nonzero=sum(1 for x in bytes(inf.read_memory(int(gdb.parse_and_eval("&LifeB[0][0]")), 64 * 64)) if x),
                 MapB_nonzero=sum(1 for x in bytes(inf.read_memory(int(gdb.parse_and_eval("&MapB[0][0]")), 64 * 64)) if x),
                 image_before=before["image"], LifeB=before["LifeB"], MapB=before["MapB"])
            MapSubsurfaceReturn(before, self.count)
        except Exception as e:
            emit("o12_384C_080E-entry-error", call=self.count, error=str(e))
        return False

class HandleLockReturn(gdb.FinishBreakpoint):
    def __init__(self):
        super().__init__(gdb.newest_frame(), internal=True)
    def stop(self):
        global active_map_image_pointer, map_image_lock_calls
        try:
            active_map_image_pointer = int(gdb.parse_and_eval("$rax"))
            map_image_lock_calls += 1
            emit("map-image-buffer-lock", pointer=active_map_image_pointer)
        except Exception as e:
            emit("map-image-buffer-lock-error", error=str(e))
        return False

class HandleLockEntry(gdb.Breakpoint):
    def __init__(self):
        super().__init__("f_171C_1B84", internal=True)
    def stop(self):
        try:
            caller = gdb.newest_frame().older()
            if caller and caller.name() == "o12_384C_080E":
                HandleLockReturn()
        except Exception as e:
            emit("map-image-buffer-lock-entry-error", error=str(e))
        return False

class MapRasterReturn(gdb.FinishBreakpoint):
    def __init__(self, before, call_number):
        super().__init__(gdb.newest_frame(), internal=True)
        self.before = before
        self.call_number = call_number
    def stop(self):
        try:
            emit("o12_384C_0B76-return", call=self.call_number,
                 mode=val("fd_3D57_07C8"), row_conversion_delta=row_counter.count - self.before["rows"],
                 bitmap_callback_delta=bitmap_counter.count - self.before["bitmaps"],
                 map_image=map_buffer_digest())
        except Exception as e:
            emit("o12_384C_0B76-return-error", call=self.call_number, error=str(e))
        return False

class MapRasterProbe(gdb.Breakpoint):
    def __init__(self):
        super().__init__("o12_384C_0B76", internal=True)
        self.count = 0
    def stop(self):
        self.count += 1
        before = {"rows": row_counter.count, "bitmaps": bitmap_counter.count}
        try:
            emit("o12_384C_0B76-entry", call=self.count, mode=val("fd_3D57_07C8"),
                 MapPlane=val("native_state_MapPlane.signed_value"), **before)
            MapRasterReturn(before, self.count)
        except Exception as e:
            emit("o12_384C_0B76-entry-error", call=self.count, error=str(e))
        return False

class CountOnly(gdb.Breakpoint):
    def __init__(self, function, event):
        super().__init__(function, internal=True)
        self.event = event
        self.count = 0
    def stop(self):
        global map_row_conversions, bitmap_calls
        self.count += 1
        if self.event == "map-row-conversion":
            map_row_conversions += 1
        elif self.event == "source-g914C-callback":
            bitmap_calls += 1
        if self.count <= 32:
            extra = {}
            if self.event in ("map-paint-entry", "map-raster-entry"):
                for expr, key in (("fd_3D57_07C8", "mode"), ("native_state_MapPlane.signed_value", "MapPlane"),
                                  ("g_2992", "previous_mode"), ("g_2994", "fresh"),
                                  ("fd_50F6_3854", "row_bytes"), ("fd_50F6_3856", "scale_x"),
                                  ("fd_50F6_3858", "scale_y"), ("fd_50F6_38C0", "side_panel")):
                    try: extra[key] = val(expr)
                    except Exception as e: extra[key] = "unavailable: " + str(e)
            emit(self.event, count=self.count, **extra)
        return False

SimEntry()
MapBuildEntry()
row_counter = CountOnly("o12_384C_03D0", "map-row-conversion")
bitmap_counter = CountOnly("source_g914C_callback", "source-g914C-callback")
map_paint_counter = CountOnly("o12_384C_100A", "map-paint-entry")
map_rows_counter = CountOnly("o12_384C_0B76", "map-raster-entry")
map_subsurface_counter = MapSubsurfaceEntry()
map_raster_probe = MapRasterProbe()
HandleLockEntry()
for bp in gdb.breakpoints() or []:
    emit("breakpoint-installed", number=bp.number, location=bp.location, enabled=bp.enabled)
def on_exit(event):
    emit("probe-summary", sim_calls=sim_calls, map_build_calls=map_build_calls,
         map_paint_calls=map_paint_counter.count, map_raster_calls=map_rows_counter.count,
         map_subsurface_build_calls=map_subsurface_counter.count,
         map_image_lock_calls=map_image_lock_calls,
         map_row_conversion_calls=row_counter.count, bitmap_callback_calls=bitmap_counter.count)
    event_file.flush()
    event_file.close()
gdb.events.exited.connect(on_exit)
emit("probe-start", executable=gdb.current_progspace().filename,
     sim_counter="DoAntSim entry/FinishBreakpoint; no inferior state writes",
     map_counter="o12_384C_0432 entry/return, row and g914C callback breakpoints")
