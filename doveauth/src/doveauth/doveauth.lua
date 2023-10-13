
-- Escape shell argument by hex encoding it and wrapping in quotes.
function escape(data)
   b16 = data:gsub(".", function(char) return string.format("%2X", char:byte()) end)
   return ("'"..b16.."'")
end

-- call out to python program to actually manage authentication for dovecot

function chatctl_verify(user, password)
    local cmd = "doveauth hexauth "..escape(user).." "..escape(password)
    print("executing: "..cmd)
    local handle = io.popen(cmd)
    local result = handle:read("*a")
    handle:close()
    return split_chatctl(result)
end

function chatctl_lookup(user) 
    assert(user)
    local handle = io.popen("doveauth hexlookup "..escape(user))
    local result = handle:read("*a")
    handle:close()
    return split_chatctl(result)
end

function get_extra_dovecot_output(res)
    return {home=res.home, uid=res.uid, gid=res.gid}
end


function auth_password_verify(request, password)
    local res = chatctl_verify(request.user, password)
    -- request:log_error("auth_password_verify "..request.user.." "..password)
    if res.status == "ok" then 
        local extra = get_extra_dovecot_output(res)
        return dovecot.auth.PASSDB_RESULT_OK, get_extra_dovecot_output(res)
    end
    return dovecot.auth.PASSDB_RESULT_PASSWORD_MISMATCH, ""
end


function auth_userdb_lookup(request)
    local res = chatctl_lookup(request.user) 
    if res.status == "ok" then
        return dovecot.auth.USERDB_RESULT_OK, get_extra_dovecot_output(res)
    end
    return dovecot.auth.USERDB_RESULT_USER_UNKNOWN, "no such user"
end

function split_chatctl(output) 
    local ret = {}
    for key, value in output:gmatch "(%w+)%s*=%s*(%w+)" do
        ret[key] = value
    end
    return ret
end
