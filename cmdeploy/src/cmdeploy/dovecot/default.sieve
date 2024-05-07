require ["imap4flags"];

# flag the message so it doesn't cause a push notification

if header :is ["Auto-Submitted"] ["auto-replied", "auto-generated"] {
	addflag "$Auto";
}
