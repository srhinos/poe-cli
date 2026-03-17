from __future__ import annotations

import zlib


def register_stubs(lua, pob_path: str) -> None:
    """Register all GUI stub functions into the Lua global namespace."""
    pob_path_lua = pob_path.replace("\\", "/")

    lua.execute("""
        GetTime = function()
            return math.floor(os.clock() * 1000)
        end
    """)

    lua.execute("""
        ConPrintf = function(fmt, ...) end
        ConExecute = function(cmd) end
        ConClear = function() end
        CopyConsoleToBuffer = function() end
    """)

    lua.execute("""
        SetWindowTitle = function(title) end
        RenderInit = function(...) end
        GetScreenSize = function() return 1920, 1080 end
        GetVirtualScreenSize = function() return 1920, 1080 end
        SetDrawLayer = function(...) end
        SetViewport = function(...) end
        SetDrawColor = function(...) end
        DrawImage = function(...) end
        DrawImageQuad = function(...) end
        DrawString = function(...) end
        DrawStringWidth = function(...) return 0 end
        DrawStringCursorIndex = function(...) return 0 end
        StripEscapes = function(s) return s end
        SetClearColor = function(...) end
        TakeScreenshot = function() end
    """)

    lua.execute("""
        do
            local imgMeta = {}
            imgMeta.__index = imgMeta
            function imgMeta:Load(path, ...) return self end
            function imgMeta:Unload() end
            function imgMeta:IsValid() return false end
            function imgMeta:IsLoading() return false end
            function imgMeta:ImageSize() return 0, 0 end
            function imgMeta:SetLoadingPriority(p) end
            function NewImageHandle()
                return setmetatable({}, imgMeta)
            end
        end
    """)

    lua.execute("""
        IsKeyDown = function(key) return false end
        GetCursorPos = function() return 0, 0 end
        SetCursorPos = function(x, y) end
        Copy = function(text) end
        Paste = function() return "" end
    """)

    lua.execute("""
        SetMainObject = function(obj)
            mainObject = obj
        end
        Restart = function() end
        Exit = function() end
        SpawnProcess = function(...) end
        LaunchSubScript = function(...) return nil end
    """)

    lua.globals()["_pobPathStr"] = pob_path_lua
    lua.execute("""
        local pobPath = _pobPathStr
        GetScriptPath = function() return pobPath end
        GetRuntimePath = function() return pobPath end
        GetUserPath = function() return pobPath end
        GetWorkDir = function() return pobPath end
        MakeDir = function(path) end
    """)

    lua.execute("""
        local pobPath = _pobPathStr

        function LoadModule(name, ...)
            local func, err = loadfile(pobPath .. "/" .. name .. ".lua")
            if not func then
                func, err = loadfile(pobPath .. "/" .. name)
            end
            if func then
                return func(...)
            else
                error("LoadModule failed: " .. tostring(err))
            end
        end

        function PLoadModule(name, ...)
            local ok, result = pcall(LoadModule, name, ...)
            if ok then
                return nil, result
            else
                return tostring(result), nil
            end
        end

        function PCall(func, ...)
            local ok, err = pcall(func, ...)
            if ok then
                return nil
            else
                return tostring(err)
            end
        end
    """)

    def py_inflate(data):
        if data is None:
            return ""
        if isinstance(data, str):
            data = data.encode("latin-1")
        try:
            return zlib.decompress(data).decode("utf-8", errors="replace")
        except (zlib.error, OSError):
            return ""

    def py_deflate(data):
        if data is None:
            return ""
        if isinstance(data, str):
            data = data.encode("utf-8")
        try:
            return zlib.compress(data).decode("latin-1")
        except (zlib.error, OSError):
            return ""

    lua.globals()["_py_inflate"] = py_inflate
    lua.globals()["_py_deflate"] = py_deflate
    lua.execute("""
        Inflate = function(data) return _py_inflate(data) end
        Deflate = function(data) return _py_deflate(data) end
    """)

    lua.execute("""
        do
            local searchMeta = {}
            searchMeta.__index = searchMeta
            function searchMeta:GetFileName() return nil end
            function searchMeta:GetSubPath() return nil end
            function searchMeta:GetFullFileName() return nil end
            function searchMeta:NextFile() return false end
            function NewFileSearch(path, allowDirs)
                return setmetatable({}, searchMeta)
            end
        end
    """)

    lua.execute("""
        local origRequire = require
        require = function(name)
            if name == "lcurl.safe" or name == "lcurl" then
                return setmetatable({}, {
                    __index = function(t, k)
                        return function() return nil, "lcurl not available in headless mode" end
                    end
                })
            end
            return origRequire(name)
        end
    """)

    lua.execute("""
        arg = arg or {}

        function isValueInTable(t, val)
            if not t then return false end
            for _, v in pairs(t) do
                if v == val then return true end
            end
            return false
        end

        function runCallback(name, ...)
            if mainObject and mainObject[name] then
                return mainObject[name](mainObject, ...)
            end
        end
    """)
