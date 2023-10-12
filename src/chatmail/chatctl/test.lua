
-- To run this test: run "lua test.lua" while in the same directory as chatctl.py

if dovecot == nil then
    dovecot = {
        auth = {
            PASSDB_RESULT_OK="PASSWORD-OK",
            PASSDB_RESULT_PASSWORD_MISMATCH="PASSWORD-MISMATCH",
            USERDB_RESULT_OK="USERDB-OK",
            USERDB_RESULT_USER_UNKNOWN="USERDB-UNKNOWN"
        }
    }
end

-- Escape shell argument by hex encoding it and wrapping in quotes.
function escape(data)
   b16 = data:gsub(".", function(char) return string.format("%2X", char:byte()) end)
   return ("'"..b16.."'")
end

-- call out to python program to actually manage authentication for dovecot

function chatctl_verify(user, password)
    local handle = io.popen("python chatctl.py hexauth "..escape(user).." "..escape(password))
    local result = handle:read("*a")
    handle:close()
    return split_chatctl(result)
end

function chatctl_lookup(user) 
    assert(user)
    local handle = io.popen("python chatctl.py hexlookup "..escape(user))
    local result = handle:read("*a")
    handle:close()
    return split_chatctl(result)
end

function get_extra_dovecot_output(res)
    return {homedir=res.homedir, uid=res.uid, gid=res.gid}
end


function auth_passdb_verify(request, password)
    local res = chatctl_verify(request.user, password)
    if res.status == "ok" then 
        return dovecot.auth.PASSDB_RESULT_OK, get_extra_dovecot_output(res)
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

-- Tests for testing the lua<->python interaction 

function test_passdb_verify_ok(user, password) 
    local res, extra = auth_passdb_verify({user=user}, password)
    assert(res==dovecot.auth.PASSDB_RESULT_OK)
    assert(extra.uid == "vmail")
    assert(extra.gid == "vmail")
    -- assert(extra.homedir == "/home/vmail/link2xt")
    print("OK test_passdb_verify_ok "..user.." "..password)
end

function test_passdb_verify_mismatch(user, password) 
    local res = auth_passdb_verify({user=user}, password)
    assert(res == dovecot.auth.PASSDB_RESULT_PASSWORD_MISMATCH)
    print("OK test_passdb_verify_mismatch "..user.." "..password)
end

function test_userdb_lookup_ok(user)
    local res, extra = auth_userdb_lookup({user=user})
    assert(extra.uid == "vmail")
    assert(extra.gid == "vmail")
    assert(res == dovecot.auth.USERDB_RESULT_OK)
    print("OK test_lookup_ok "..user)
end

function test_split_chatctl()
    local res = split_chatctl("a=3 b=4\nc=5")
    assert(res["a"] == "3")
    assert(res["b"] == "4")
    assert(res["c"] == "5")
    print("OK test_split_chatctl")
end 

test_split_chatctl()
test_passdb_verify_ok("link2xt@instant2.testrun.org", "Ahyei6ie")
test_passdb_verify_mismatch("link2xt@instant2.testrun.org", "Aqwlek")
test_userdb_lookup_ok("link2xt@instant2.testrun.org")

