
require "doveauth"

-- simulate dovecot defined result codes 

dovecot = {
    auth = {
        PASSDB_RESULT_OK="PASSWORD-OK",
        PASSDB_RESULT_PASSWORD_MISMATCH="PASSWORD-MISMATCH",
        USERDB_RESULT_OK="USERDB-OK",
        USERDB_RESULT_USER_UNKNOWN="USERDB-UNKNOWN"
    }
}


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
    print("OK test_userdb_lookup_ok "..user)
end

function test_userdb_lookup_mismatch(user)
    local res, extra = auth_userdb_lookup({user=user})
    assert(res == dovecot.auth.USERDB_RESULT_USER_UNKNOWN)
    print("OK test_userdb_lookup_mismatch "..user)
end

function test_passdb_lookup_ok(user)
    local res, extra = auth_passdb_lookup({user=user})
    assert(extra.uid == "vmail")
    assert(extra.gid == "vmail")
    assert(res == dovecot.auth.PASSDB_RESULT_OK)
    print("OK test_passdb_lookup_ok "..user)
end

function test_passdb_lookup_mismatch(user)
    local res, extra = auth_passdb_lookup({user=user})
    assert(res == dovecot.auth.PASSDB_RESULT_USER_UNKNOWN)
    print("OK test_passdb_lookup_mismatch "..user)
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
test_userdb_lookup_mismatch("wlekqjlew@xyz.org")
test_passdb_lookup_ok("link2xt@instant2.testrun.org")
test_passdb_lookup_mismatch("llqkwjelqwe@xyz.org")

