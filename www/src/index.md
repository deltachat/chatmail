
<img class="banner" src="collage-top.png"/>

## Dear [Delta Chat](https://get.delta.chat) users and newcomers ... 

{% if config.mail_domain != "nine.testrun.org" %}
Welcome to instant, interoperable and [privacy-preserving](privacy.html) messaging :) 
{% else %}
Welcome to the default onboarding server ({{ config.mail_domain }}) 
for Delta Chat users.  For details how it avoids storing personal information
please see our [privacy policy](privacy). 
{% endif %}

👉 **Tap** or scan this QR code to get a `@{{config.mail_domain}}` chat profile

<a href="DCACCOUNT:https://{{ config.mail_domain }}/new">
    <img width=300 style="float: none;" src="qr-chatmail-invite-{{config.mail_domain}}.png" /></a>

🐣 **Choose** your Avatar and Name

💬 **Start** chatting with any Delta Chat contacts using [QR invite codes](https://delta.chat/en/help#howtoe2ee)

{% if config.mail_domain != "nine.testrun.org" %}
<div class="experimental">Note: this is only a temporary development chatmail service</div>
{% endif %}
