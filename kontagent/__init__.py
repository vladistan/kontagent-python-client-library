# Kontagent Analytics API interface

import random
import urllib
import httplib
import datetime
import threading
import simplejson
from urlparse import urlparse, urlunparse

DIRECTED_VAL = 'd'
UNDIRECTED_VAL = 'u'

class AnalyticsQuery:
    """ Class representing a single query to the Kontagent Analytics API. """
    def __init__(self, query_string, api_server, query_type=None):
        """ AnalyticsQuery constructor.

        Keyword arguments:
        query_string -- query string in the form /api/<version number>/<apikey>/<message type>/?<key>=<data>&<keyn>=<datan>
        api_server -- api server that this message will be sent to when send() or thread_send() is called.
                      eg. 'api.geo.kontagent.net'
        query_type -- optional argument containing the type of the query, eg. 'ins'.
                      This is useful when you need to identify the type of a query
                      without having to parse the query string.

        """
        self.query = query_string
        self.server =  api_server
        self.query_type = query_type
        
    def send(self):
        """Sends the query to the api server

        Returns HTTP response.

        """
        conn = httplib.HTTPConnection(self.server)
        conn.request("GET", self.query)
        response = conn.getresponse()
        data = response.read()
        conn.close()
        return data

    def thread_send(self):
        """Sends the query to the api server in a seperate thread.

        Returns instantly.

        """                
        t = threading.Thread(target=self.send)
        t.setDaemon(True)
        t.start()
        return


class AnalyticsInterface:
    """The AnalyticsInterface class is a factory for AnalyticsQuery objects.

    This class stores information about the api server, such as
    address, api key, and server version, to allow for easy construction
    of AnalyticsQuery objects.

    Usage:
     analytics_interface = AnalyticsInterface('test-server.kontagent.com')

    """
    
    def __init__(self, api_server, api_key, api_version="v1"):       
        self.server = api_server
        self.key = api_key
        self.version = api_version

    def construct_query(self, msg_type, parameters):
        """ Constructs an AnalyticsQuery object with a query string in the form:
        /api/<version number>/<apikey>/<message type>/?<key>=<data>&<keyn>=<datan>

        Returns the AnalyticsQuery object.
        
        Keyword arguments:
        msg_type --  a string containing the message type.(ie. 'cpu')
        parameters --  a dictionary containing the query parameters                       

        """
        return AnalyticsQuery("/api/" + self.version + "/" + self.key \
                         + "/" + msg_type +"/?" + urllib.urlencode(parameters),
                         self.server, msg_type)

                           
    def user_info(self, uid, birthyear=None, gender=None, city=None,
                 country=None, state=None, postal=None, friends=None):
        """ Generates a User Information (cpu) Analytics REST API call. """
        
        params =  {"s":uid, "b":birthyear, "g":gender, "ly":city,
                   "lc":country, "ls":state, "lp":postal, "f":friends}
        params = dict((k, v) for k, v in params.iteritems() if v is not None)

        return self.construct_query("cpu", params)
    

    def application_added(self, uid, trackingTag=None, shortTrackingTag=None):
        """Generates an Application Added (apa) Analytics REST API call."""


        params = {"s":uid, "u":trackingTag, "su":shortTrackingTag}
        params = dict((k, v) for k, v in params.iteritems() if v is not None)
        
        return self.construct_query("apa", params)

    def application_removed(self, uid):
        """Generates an Application Removed (apr) Analytics REST API call."""

        params = {"s":uid}

        return self.construct_query("apr", params)

    
    def page_request(self, uid, uri, requester_ip=None):
        """Generates a Page Request (pgr) Analytics REST API call."""

        params = {"s":uid, "u":uri, "ip":requester_ip}
        params = dict((k, v) for k, v in params.iteritems() if v is not None)

        return self.construct_query("pgr", params)

    def invite_sent(self, uid, recipients, tracking_tag=None, 
                    template_id=None, subtype_1=None, subtype_2=None,
                    subtype_3=None):
        """Generates an Invite Sent (ins) Analytics REST API call."""

        if tracking_tag is None:
            tracking_tag = generate_long_tag()

        recipient_string = None
        for recipient in recipients:
            recipient_string =  str(recipient) + ','
        recipient_string = recipient_string.rstrip(',')
        params = {"s":uid, "r":recipient_string, "t":template_id,
                  "u":tracking_tag, "st1":subtype_1, "st2":subtype_2,
                  "st3":subtype_3}
        params = dict((k, v) for k, v in params.iteritems() if v is not None)

        return self.construct_query("ins", params)

    def notification_sent(self, uid, recipients, tracking_tag,
                          template_id=None, subtype_1=None, subtype_2=None):
        """Generates a Notification Sent (nts) Analytics REST API call."""
        recipient_string = None
        for recipient in recipients:
            recipient_string =  str(recipient) + ','
        recipient_string = recipient_string.rstrip(',')
        params = {"s":uid, "r":recipient_string, "t":template_id,
                  "u":tracking_tag, "st1":subtype_1, "st2":subtype_2}
        params = dict((k, v) for k, v in params.iteritems() if v is not None)

        return self.construct_query("nts", params)

    def email_sent(self, sender, recipients, tracking_tag,
                   template_id=None, subtype_1=None, subtype_2=None):
        """Generates an Email Notification Sent (nes) Analytics REST API call."""
        recipient_string = None
        for recipient in recipients:
            recipient_string =  str(recipient) + ','
        recipient_string = recipient_string.rstrip(',')
        params = {"s":sender, "r":recipient_string, "t":template_id,
                  "u":tracking_tag, "st1":subtype_1, "st2":subtype_2}
        params = dict((k, v) for k, v in params.iteritems() if v is not None)

        return self.construct_query("nes", params)
        
    def feed_post(self, poster, template_id=None, post_type=None,
                  subtype_1=None, subtype_2=None):
        """Generates a Feed Post (fdp) Analytics REST API call."""
        params = {"s":poster, "t":template_id, "pt":post_type, "tu":"fdp",
                  "st1":subtype_1, "st2":subtype_2}
        params = dict((k, v) for k, v in params.iteritems() if v is not None)   

        return self.construct_query("fdp", params)

    def invite_response(self, installed, tracking_tag, template_id=None,
                        recipient_id=None, subtype_1=None, subtype_2=None,
                        subtype_3=None):
        """Generates an Invite Click Response (inr) Analytics REST API call."""
        params = {"r":recipient_id, "i":installed, "t":template_id,
                  "u":tracking_tag, "tu":"inr", "st1":subtype_1,
                  "st2":subtype_2, "st3":subtype_3}
        params = dict((k, v) for k, v in params.iteritems() if v is not None)

        return self.construct_query("inr", params)

    def notification_response(self, installed, tracking_tag, template_id=None,
                              recipient_id=None, subtype_1=None, subtype_2=None,
                              subtype_3=None):
        """Generates an Notification Click Response (ntr) Analytics REST API call."""
        params = {"r":recipient_id, "i":installed, "t":template_id,
                  "u":tracking_tag, "tu":"ntr", "st1":subtype_1,
                  "st2":subtype_2, "st3":subtype_3}
        params = dict((k, v) for k, v in params.iteritems() if v is not None)      

        return self.construct_query("ntr", params)

    # Check
    def email_response(self, installed, tracking_tag, recipient_id=None,
                       subtype_1=None, subtype_2=None, subtype_3=None):
        """Generates an Email Click Response (nei) Analytics REST API call."""
        params = {"r":recipient_id, "i":installed, "u":tracking_tag,
                  "tu":"nei", "st1":subtype_1, "st2":subtype_2, "st3":subtype_3}
        params = dict((k, v) for k, v in params.iteritems() if v is not None)

        return self.construct_query("nei", params)

    def ucc(self, uid, type, installed, short_tracking_tag=None,
            subtype_1=None, subtype_2=None, subtype_3=None):
        """Generates an Undirected Communication Click (ucc) Analytics REST API call."""
        params   = {"s":uid, "tu":type, "i":installed, "su":short_tracking_tag,
                    "st1":subtype_1, "st2":subtype_2, "st3":subtype_3}
        params = dict((k, v) for k, v in params.iteritems() if v is not None)   
        
        return self.construct_query("ucc", params)
    
    def goal_count(self, uid, gc_num, gc_value):
        """Generates a Goal Count (gci) Analytics REST API call."""
        params = {"s":uid}
        params["gc%d" % gc_num] = gc_value

        return self.construct_query("gci", params)

            
def construct_query(api_key, api_server, api_version, msg_type, parameters):
    """Constructs a generic query to the analytics API in the form:

    /api/<version number>/<apikey>/<message type>/?<key>=<data>
    
    Keyword arguments:
    apikey --  Kontagent API key
    api_server -- Kontagent API server, eg. api.geo.kontagent.net
    api_version -- <version number>
    msg_type --  <message type>, eg. 'ins', 'apa', etc.
    parameters --  a dictionary containing the variables in the call
    
    """
    return AnalyticsQuery( "/api/" + api_version + "/" + api_key \
                           + "/" + msg_type + "/?" + urllib.urlencode(parameters),
                           api_server)


def generate_long_tag():
    """ Generates a long tracking tag.

    Returns a 16 character tracking tag.

    """
    return "%X" % random.getrandbits(64)


def generate_short_tag():
    """ Generates a short tracking tag.

    Returns an 8 character tracking tag.

    """
    return "%X" % random.getrandbits(32)


def append_params(url, params):
    """ Appends GET parameters onto an arbitrary URL.

    Keyword arguments:
    url -- string containing the original URL, eg. 'http://apps.facebook.com/yourapp/?foo=bar'
    params -- dictionary containing additional GET params to append to the original url

    """
    params = dict((k, v) for k, v in params.iteritems() if v is not None)
    old_url = urlparse(url)
    old_params = parse_qs(old_url[4], True)
    old_params.update(params)
    new_url = []
    for item in old_url:
        new_url.append(item)
    new_url[4] = urllib.urlencode(old_params, True)
    if new_url[2] == '' and new_url[4] != '':
        new_url[2] = '/'    
    return urlunparse(new_url)


def strip_params(url):
    """ Removes Kontagent parameters from a URL.

    This strips kt_type, kt_ut, kt_d, kt_t, kt_st1, kt_st2, kt_st3
    params from the given url and returns the new URL.

    This is used after processing a URL with kontagent params; the user
    is redirected to the stripped URL. This is to prevent the user from
    refreshing the page and causing another message to be sent to Kontagent.

    Keyword arguments:
    url -- url to remove Kontagent parameters from

    """
    old_url = urlparse(url)
    old_params = parse_qs(old_url[4], True)

    for k,v in old_params.items():
        if k == 'kt_type' or \
           k == 'kt_ut' or \
           k == 'kt_d' or \
           k == 'kt_t' or \
           k == 'kt_st1' or \
           k == 'kt_st2' or \
           k == 'kt_st3':
            del old_params[k]
    
    new_url = []
    for item in old_url:
        new_url.append(item)
    new_url[4] = urllib.urlencode(old_params, True)
    if new_url[2] == '' and new_url[4] != '':
        new_url[2] = '/'    
    return urlunparse(new_url)


def append_invite_content_params(url,
                                tracking_tag,
                                template=None,
                                subtype1=None,
                                subtype2=None,
                                subtype3=None):
    """ Appends invite click tracking parameters to a URL.

    This method should be called on any links back to your application
    inside the 'content' parameter in an <fb:request-form>.

    Use the same tracking_tag for each append_invite_content_params and
    append_invite_action_params call you make related to this invite session.

    Returns the original URL with kt_type, kt_ut, kt_d, kt_t, and kt_stN parameters appended.

    Keyword arguments:
    url -- original url, should point to the landing page for your invite, eg. 'http://apps.facebook.com/yourapp/'
    tracking_tag -- unique tracking tag generated with generate_long_tag(). You must use
                    the same unique tracking ID here as you use for any other
                    append_invite_content_params and append_invite_action_params calls
                    that you make for this <fb:request-form>.
    template -- A/B testing template ID
    subtypeN -- subtypeN value

    """
    kt_params = {'kt_type' : 'in',
                 'kt_ut' : tracking_tag,
                 'kt_d' : DIRECTED_VAL,
                 'kt_t' : template,
                 'kt_st1' : subtype1,
                 'kt_st2' : subtype2,
                 'kt_st3' : subtype3}
    return append_params(url, kt_params)


def append_invite_action_params(url,
                                tracking_tag,
                                template=None,
                                subtype1=None,
                                subtype2=None,
                                subtype3=None):
    """ Appends invite sent tracking parameters to a URL.

    This method should be called on any links back to your application
    inside the 'action' parameter in an <fb:request-form>.

    Use the same tracking_tag for each append_invite_content_params and
    append_invite_action_params call you make related to this invite session.

    Returns the original URL with kt_type, kt_ut, kt_t, and kt_stN parameters appended.

    Keyword arguments:
    url -- original url, should point to the page you want to redirect your user to after they send an invite
    tracking_tag -- unique tracking tag generated with generate_long_tag(). You must use
                    the same unique tracking ID here as you use for any other
                    append_invite_content_params and append_invite_action_params calls
                    that you make for this <fb:request-form>.
    template -- A/B testing template ID
    subtypeN -- subtypeN value

    """  
    kt_params = {'kt_type' : 'ins',
                 'kt_ut' : tracking_tag,
                 'kt_t' : template,
                 'kt_st1' : subtype1,
                 'kt_st2' : subtype2,
                 'kt_st3' : subtype3}
    return append_params(url, kt_params)
    

def append_notification_tracking(url,
                                 template=None,
                                 subtype1=None,
                                 subtype2=None,
                                 subtype3=None):
    """ Appends notification tracking parameters to a URL.

    This method should be called on any links inside a notification that
    point back to your application.

    Returns the original URL with kt_type, kt_ut, kt_t, and kt_stN parameters appended.
    
    Keyword arguments:
    url -- original url
    template -- A/B testing template ID
    subtypeN -- subtypeN value

    """
    kt_params = {'kt_type' : 'nt',
                 'kt_ut' : generate_long_tag(),
                 'kt_t' : template,
                 'kt_st1' : subtype1,
                 'kt_st2' : subtype2,
                 'kt_st3' : subtype3}
    return append_params(url, kt_params)


# Utility functions from urlparse python2.6
_hextochr = dict(('%02x' % i, chr(i)) for i in range(256))
_hextochr.update(('%02X' % i, chr(i)) for i in range(256))

def unquote(s):
    """unquote('abc%20def') -> 'abc def'."""
    res = s.split('%')
    for i in xrange(1, len(res)):
        item = res[i]
        try:
            res[i] = _hextochr[item[:2]] + item[2:]
        except KeyError:
            res[i] = '%' + item
        except UnicodeDecodeError:
            res[i] = unichr(int(item[:2], 16)) + item[2:]
    return "".join(res)

def parse_qs(qs, keep_blank_values=0, strict_parsing=0):
    """Parse a query given as a string argument.

        Arguments:

        qs: URL-encoded query string to be parsed

        keep_blank_values: flag indicating whether blank values in
            URL encoded queries should be treated as blank strings.
            A true value indicates that blanks should be retained as
            blank strings.  The default false value indicates that
            blank values are to be ignored and treated as if they were
            not included.

        strict_parsing: flag indicating what to do with parsing errors.
            If false (the default), errors are silently ignored.
            If true, errors raise a ValueError exception.
    """
    dict = {}
    for name, value in parse_qsl(qs, keep_blank_values, strict_parsing):
        if name in dict:
            dict[name].append(value)
        else:
            dict[name] = [value]
    return dict

def parse_qsl(qs, keep_blank_values=0, strict_parsing=0):
    """Parse a query given as a string argument.

    Arguments:

    qs: URL-encoded query string to be parsed

    keep_blank_values: flag indicating whether blank values in
        URL encoded queries should be treated as blank strings.  A
        true value indicates that blanks should be retained as blank
        strings.  The default false value indicates that blank values
        are to be ignored and treated as if they were  not included.

    strict_parsing: flag indicating what to do with parsing errors. If
        false (the default), errors are silently ignored. If true,
        errors raise a ValueError exception.

    Returns a list, as G-d intended.
    """
    pairs = [s2 for s1 in qs.split('&') for s2 in s1.split(';')]
    r = []
    for name_value in pairs:
        if not name_value and not strict_parsing:
            continue
        nv = name_value.split('=', 1)
        if len(nv) != 2:
            if strict_parsing:
                raise ValueError, "bad query field: %r" % (name_value,)
            # Handle case of a control-name with no equal sign
            if keep_blank_values:
                nv.append('')
            else:
                continue
        if len(nv[1]) or keep_blank_values:
            name = unquote(nv[0].replace('+', ' '))
            value = unquote(nv[1].replace('+', ' '))
            r.append((name, value))

    return r
