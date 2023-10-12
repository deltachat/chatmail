
dovecot = {
    auth = {
        PASSDB_RESULT_OK="OK",
        PASSDB_RESULT_PASSWORD_MISMATCH="MISMATCH"
    }
}

-- Escape shell argument by hex encoding it and wrapping in quotes.
function escape(data)
   b16 = data:gsub(".", function(char) return string.format("%2X", char:byte()) end)
   return ("'"..b16.."'")
end

function chatctl_verify(user, password)
    return os.execute("python chatctl.py hexauth "..escape(user).." "..escape(password))
end

function chatctl_lookup(hex, user) 
    return os.execute("python chatctl.py hexlookup "..escape(user))
end


function auth_password_verify(request, password)
    if chatctl_verify(request.user, password) then
        return dovecot.auth.PASSDB_RESULT_OK, {}
    end
    return dovecot.auth.PASSDB_RESULT_PASSWORD_MISMATCH, ""
end

function auth_passdb_lookup(request)
    if chatctl_lookup(request.user) then
        return dovecot.auth.PASSDB_RESULT_OK, {}
    end
    return dovecot.auth.PASSDB_RESULT_USER_UNKNOWN, "no such user"
end

function auth_userdb_lookup(request)
    if chatctl_lookup(request.user) then
        return dovecot.auth.USERDB_RESULT_OK, "uid=vmail gid=vmail"
    end
    return dovecot.auth.USERDB_RESULT_USER_UNKNOWN, "no such user"
end

function split_chatctl_results(output) 
    local ret = {}
    for key, value in output:gmatch "(%w+)%s*=%s*(%w+)" do
        ret[key] = value
    end
    return ret
end

local res = auth_password_verify({user="link2xt@instant2.testrun.org"}, "Ahyei6ie")
print(res)

