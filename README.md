XOAUth
======

It 's been sometime that Google and other providers have started to support XOAuth authentication for their mail services.

Get started
-----------

It is quite easy to get started. 
First of all when you the OAuth dance you have to ask permissions (or add the scope) for the Mail service. In the case of Gmail you can do this:

> GOOGLE_OAUTH_SETTINGS = {
>  'SCOPES':  ['https://mail.google.com/']
> }

Then the OAuth tokens that will be generated will be good to be used for this scope as well. You can have multiple scopes for the same tokens such as Google Contacts or Google Calendar.

IMAP Authentication
-------------------
After the user has successfully authorized your app all you have to do is to use them in order to connect to the IMAP server. Using this python code all you have to do is a one liner:

> import xoauth
> imap_conn = connect_to_gmail(CREDENTIALS, user)

Where credentials is a tuple holding the OAuth consumer and secret key and user is a dict containing the g_oauth_token, g_oauth_token_secret and email of the user.