
<img class="banner" src="collage-info.png"/>

## More information 

`nine.testrun.org` provides a low-maintenance, resource efficient and 
interoperable e-mail service for everyone. What's behind a `chatmail` is 
effectively a normal e-mail address just like any other but optimized 
for the usage in chats, especially DeltaChat.

### Choosing a chatmail address instead of using a random one

In the Delta Chat account setup 
you may tap `LOG INTO YOUR E-MAIL ACCOUNT` 
and fill the two fields like this: 

- `Address`: invent a word with
{% if username_min_length == username_max_length %}
  *exactly* {{ username_min_length }}
{% else %}
  {{ username_min_length}}
  {% if username_max_length == "more" %}
    or more
  {% else %}
    to {{ username_max_length }}
  {% endif %}
{% endif %}
  characters
  and append `@{{config.mail_domain}}` to it.

- `Password`: invent at least {{ password_min_length }} characters.

If the e-mail address is not yet taken, you'll get that account. 
The first login sets your password. 


### Rate and storage limits 

- Un-encrypted messages are blocked to recipients outside
  {{config.mail_domain}} but setting up contact via [QR invite codes](https://delta.chat/en/help#howtoe2ee) 
  allows your messages to pass freely to any outside recipients.

- You may send up to {{ config.max_user_send_per_minute }} messages per minute.

- Seen messages are removed {{ delete_mails_after }} after arriving on the server.

- You can store up to [{{ config.max_mailbox_size }} messages on the server](https://delta.chat/en/help#what-happens-if-i-turn-on-delete-old-messages-from-server).


### Who are the operators? Which software is running? 

This chatmail provider is run by a small voluntary group of devs and sysadmins,
who [publically develop chatmail provider setups](https://github.com/deltachat/chatmail).
Chatmail setups aim to be very low-maintenance, resource efficient and 
interoperable with any other standards-compliant e-mail service. 
