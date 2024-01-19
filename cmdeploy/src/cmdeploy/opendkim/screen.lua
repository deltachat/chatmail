-- Ignore signatures that do not correspond to the From: domain.

from_domain = odkim.get_fromdomain(ctx)
if from_domain == nil then
	return nil
end

n = odkim.get_sigcount(ctx)
if n == nil then
	return nil
end

for i = 1, n do
	sig = odkim.get_sighandle(ctx, i - 1)
	sig_domain = odkim.sig_getdomain(sig)
	if from_domain ~= sig_domain then
		odkim.sig_ignore(sig)
	end
end

return nil
