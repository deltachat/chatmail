require ["imap4flags"];

if header :is ["Auto-Submitted"] ["auto-replied", "auto-generated"] {
	addflag "$Auto";
}
