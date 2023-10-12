
-- To run this test: run "lua test.lua" while in the same directory as chatctl.py

if dovecot == nil then
    dovecot = {
        auth = {
            PASSDB_RESULT_OK="OK",
            PASSDB_RESULT_PASSWORD_MISMATCH="MISMATCH"
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

function split_chatctl(output) 
    local ret = {}
    for key, value in output:gmatch "(%w+)%s*=%s*(%w+)" do
        ret[key] = value
    end
    return ret
end

-- Tests for testing the lua<->python interaction 

function test_verify_ok(user, password) 
    local res = auth_password_verify({user=user}, password)
    assert(res=="OK")
    print("OK test_verify_ok "..user.." "..password)
end

function test_verify_mismatch(user, password) 
    local res = auth_password_verify({user=user}, password)
    assert(res == "MISMATCH")
    print("OK test_verify_mismatch "..user.." "..password)
end

function test_split_chatctl()
    local res = split_chatctl("a=3 b=4\nc=5")
    assert(res["a"] == "3")
    assert(res["b"] == "4")
    assert(res["c"] == "5")
    print("OK test_split_chatctl")
end 

test_split_chatctl()
test_verify_ok("link2xt@instant2.testrun.org", "Ahyei6ie")
test_verify_mismatch("link2xt@instant2.testrun.org", "Aqwlek")

