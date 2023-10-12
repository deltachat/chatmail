-- Lua based authentication script for Dovecot.
--
-- It calls external chatctl command to answer requests.

-- Hexadecimal aka base16 encoding.
function hex(data)
   return (data:gsub(".", function(char) return string.format("%2X", char:byte()) end))
end

-- Escape shell argument by hex encoding it and wrapping in quotes.
function escape(data)
   return ("'"..hex(data).."'")
end

function auth_password_verify(request, password)
  if os.execute("/home/vmail/chatctl hexauth "..escape(request.user).." "..escape(password)) then
    return dovecot.auth.PASSDB_RESULT_OK, {}
  end
  return dovecot.auth.PASSDB_RESULT_PASSWORD_MISMATCH, ""
end

function auth_passdb_lookup(request)
  if os.execute("/home/vmail/chatctl hexlookup "..escape(request.user)) then
    return dovecot.auth.PASSDB_RESULT_OK, {}
  end
  return dovecot.auth.PASSDB_RESULT_USER_UNKNOWN, "no such user"
end

function auth_userdb_lookup(request)
  if os.execute("/home/vmail/chatctl hexlookup "..escape(request.user)) then
    return dovecot.auth.USERDB_RESULT_OK, "uid=vmail gid=vmail"
  end

  return dovecot.auth.USERDB_RESULT_USER_UNKNOWN, "no such user"
end
