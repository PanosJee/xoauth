# encoding: utf-8
#!/usr/bin/pypy
#
# Code to authenicate with xoauth against Gmail originally written by Google Inc.
#
# Copyright 2010 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Modified by Panayiotis Papadopoulos at SocialCaddy LLC 2010
#

import imaplib
import random
import base64
import urllib
import hmac
import time
import sha

class OAuthEntity(object):
  """Represents consumers and tokens in OAuth."""

  def __init__(self, key, secret):
    self.key = key
    self.secret = secret

def UrlEscape(text):
  # See OAUTH 5.1 for a definition of which characters need to be escaped.
  return urllib.quote(text, safe='~-._')


def UrlUnescape(text):
  # See OAUTH 5.1 for a definition of which characters need to be escaped.
  return urllib.unquote(text)
	
def FormatUrlParams(params):
  """Formats parameters into a URL query string.

  Args:
    params: A key-value map.

  Returns:
    A URL query string version of the given parameters.
  """
  param_fragments = []
  for param in sorted(params.iteritems(), key=lambda x: x[0]):
    param_fragments.append('%s=%s' % (param[0], UrlEscape(param[1])))
  return '&'.join(param_fragments)
	
def EscapeAndJoin(elems):
  return '&'.join([UrlEscape(x) for x in elems])

def GenerateSignatureBaseString(method, request_url_base, params):
  """Generates an OAuth signature base string.

  Args:
    method: The HTTP request method, e.g. "GET".
    request_url_base: The base of the requested URL. For example, if the
      requested URL is
      "https://mail.google.com/mail/b/xxx@googlemail.com/imap/?" +
      "xoauth_requestor_id=xxx@googlemail.com", the request_url_base would be
      "https://mail.google.com/mail/b/xxx@googlemail.com/imap/".
    params: Key-value map of OAuth parameters, plus any parameters from the
      request URL.

  Returns:
    A signature base string prepared according to the OAuth Spec.
  """
  return EscapeAndJoin([method, request_url_base, FormatUrlParams(params)])

def GenerateXOauthString(consumer, access_token, user, proto,
                         xoauth_requestor_id, nonce, timestamp):
	"""Generates an IMAP XOAUTH authentication string.

	Args:
	  consumer: An OAuthEntity representing the consumer.
	  access_token: An OAuthEntity representing the access token.
	  user: The Google Mail username (full email address)
	  proto: "imap" or "smtp", for example.
	  xoauth_requestor_id: xoauth_requestor_id URL parameter for 2-legged OAuth
	  nonce: optional supplied nonce
	  timestamp: optional supplied timestamp

	Returns:
	  A string that can be passed as the argument to an IMAP
	  "AUTHENTICATE XOAUTH" command after being base64-encoded.
	"""
	method = 'GET'
	url_params = {}
	if xoauth_requestor_id:
	  url_params['xoauth_requestor_id'] = xoauth_requestor_id
	oauth_params = {}
	FillInCommonOauthParams(oauth_params, consumer, nonce, timestamp)
	if access_token.key:
	  oauth_params['oauth_token'] = access_token.key
	signed_params = oauth_params.copy()
	signed_params.update(url_params)
	request_url_base = (
	    'https://mail.google.com/mail/b/%s/%s/' % (user, proto))
	base_string = GenerateSignatureBaseString(
	    method,
	    request_url_base,
	    signed_params)
	signature = GenerateOauthSignature(base_string, consumer.secret,
	                                   access_token.secret)
	oauth_params['oauth_signature'] = signature

	formatted_params = []
	for k, v in sorted(oauth_params.iteritems()):
	  formatted_params.append('%s="%s"' % (k, UrlEscape(v)))
	param_list = ','.join(formatted_params)
	if url_params:
	  request_url = '%s?%s' % (request_url_base,
	                           FormatUrlParams(url_params))
	else:
	  request_url = request_url_base
	preencoded = '%s %s %s' % (method, request_url, param_list)
	return preencoded

def FillInCommonOauthParams(params, consumer, nonce=None, timestamp=None):
	"""Fills in parameters that are common to all oauth requests.

	Args:
	  params: Parameter map, which will be added to.
	  consumer: An OAuthEntity representing the OAuth consumer.
	  nonce: optional supplied nonce
	  timestamp: optional supplied timestamp
	"""
	params['oauth_consumer_key'] = consumer.key
	if nonce:
	  params['oauth_nonce'] = nonce
	else:
	  params['oauth_nonce'] = str(random.randrange(2**64 - 1))
	params['oauth_signature_method'] = 'HMAC-SHA1'
	params['oauth_version'] = '1.0'
	if timestamp:
	  params['oauth_timestamp'] = timestamp
	else:
	  params['oauth_timestamp'] = str(int(time.time()))

def GenerateHmacSha1Signature(text, key):
  digest = hmac.new(key, text, sha)
  return base64.b64encode(digest.digest())

def GenerateOauthSignature(base_string, consumer_secret, token_secret):
	key = EscapeAndJoin([consumer_secret, token_secret])
	return GenerateHmacSha1Signature(base_string, key)

def connect_to_gmail(CREDENTIALS, email, oauth_token, oauth_token_secret):
    """
    Call this function to get an authenticated IMAP connection
    """
    consumer = OAuthEntity(CREDENTIALS[0], CREDENTIALS[1])
    access_token = OAuthEntity(oauth_token, oauth_token_secret)
    xoauth_string = GenerateXOauthString(
      consumer, access_token, email, 'imap',
      None, str(random.randrange(2**64 - 1)), str(int(time.time())))

    # connect to imap
    imap_conn = imaplib.IMAP4_SSL('imap.googlemail.com')
    #imap_conn.debug = 3
    imap_conn.authenticate('XOAUTH', lambda x: xoauth_string)
    imap_conn.select('INBOX')
    
    return imap_conn
