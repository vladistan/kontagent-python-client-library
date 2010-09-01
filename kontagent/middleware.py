from kontagent import AnalyticsInterface, strip_params
from django.http import HttpResponse
from django.conf import settings


def callback_to_facebook(url):
    """ Changes a URL that points directly to your callback to a URL that points to facebook
    
    Ex. http://caseybanner.ca:10000/fb/canvas/some_page/?foo=bar changes to:
    http://apps.facebook.com/my_app/some_page/?foo=bar
    
    Keyword arguments:
    url -- the URL to convert
    """
    return url.replace(settings.FACEBOOK_CALLBACK_HOST + settings.FACEBOOK_CALLBACK_PATH,
                       "http://apps.facebook.com/%s/" % settings.FACEBOOK_APP_NAME)

def get_kt_params(request):    
    tracking = request.GET.get('kt_ut', None)
    template = request.GET.get('kt_t', None)
    subtype1 = request.GET.get('kt_st1', None)
    subtype2 = request.GET.get('kt_st2', None)
    subtype3 = request.GET.get('kt_st3', None)

    return {'u' : tracking,
            't' : template,
            'st1' : subtype1,
            'st2' : subtype2,
            'st3' : subtype3}

def get_uid(request):
    uid = None
    if 'fb_sig_canvas_user' in request.POST:
        uid = request.POST['fb_sig_canvas_user']
    elif 'fb_sig_user' in request.POST:
        uid = request.POST['fb_sig_user']
    elif 'fb_sig_user' in request.GET:
        uid = request.GET['fb_sig_user']
    elif 'fb_sig_user' in request.GET:
        uid = request.GET['fb_sig_user']
    return uid
    
def facebook_redirect(url):
    response = HttpResponse("<fb:redirect url=\"%s\"/>" % url)
    return response


class KontagentMiddleware:
    """ This is django compatible middleware.

    This does not depend on pyfacebook, however, if you are using pyFacebook,
    include this middleware before the  pyfacebook middleware.

    Note: currently facebook signature checking is not done.

    """

    def __init__(self, auto_redirect=True):
        """ Initializer for Kontagent Django middleware.

        Keyword arguments:
        auto_redirect -- indicates if we should automatically strip Kontagent
                         tracking parameters off request URLs and redirect to the
                         stripped URL. This is recommended so that messages
                         don't get sent twice if a user refreshes the page
                         after following a link with kontagent params.
        """
        self.redirect = auto_redirect
        self.analytics_interface = AnalyticsInterface(settings.KONTAGENT_API_SERVER,
                                                      settings.KONTAGENT_API_KEY)


    def process_request(self, request):
        # Check for app removal
        if 'fb_sig_uninstall' in request.POST and get_uid(request) is not None:
            if request.POST['fb_sig_uninstall'] == '1':
                self.analytics_interface.application_removed(get_uid(request)).thread_send()

        # Check for app added
        #and 'kt_ut' in request.GET \
        if 'installed' in request.GET and request.GET['installed'] == '1' \
               and get_uid(request) is not None:
            kt_params = get_kt_params(request)
            self.analytics_interface.application_added(uid=get_uid(request),
                                                       trackingTag=kt_params['u']).thread_send()

        # Process tracking params
        kt_type = request.GET.get('kt_type', None)
        if kt_type is not None:
            # Notification Click
            if kt_type == "nt":
                if 'kt_ut' in request.GET and 'installed' not in request.GET:
                    installed = request.GET.get('fb_sig_added', False)
                    kt_params = get_kt_params(request)
                    uid = get_uid(request)
                        
                    self.analytics_interface.notification_response(installed=installed,
                                                                   recipient_id=uid,
                                                                   tracking_tag=kt_params['u'],
                                                                   template_id=kt_params['t'],
                                                                   subtype_1=kt_params['st1'],
                                                                   subtype_2=kt_params['st2'],
                                                                   subtype_3=kt_params['st3']).thread_send()
                    
                    if self.redirect:
                        return facebook_redirect(callback_to_facebook(strip_params(request.build_absolute_uri())))
                    
            # Invite sent
            elif kt_type == "ins":
                if 'fb_sig_user' in request.POST \
                       and 'ids[]' in request.POST and 'kt_ut' in request.GET:
                    uid = get_uid(request)
                    uids = request.POST.getlist('ids[]')
                    kt_params = get_kt_params(request)

                    self.analytics_interface.invite_sent(uid=uid,
                                                         recipients=uids,
                                                         tracking_tag=kt_params['u'],
                                                         template_id=kt_params['t'],
                                                         subtype_1=kt_params['st1'],
                                                         subtype_2=kt_params['st2'],
                                                         subtype_3=kt_params['st3']).thread_send()

            # Invite click
            elif kt_type == "in":
                if 'kt_ut' in request.GET and 'fb_sig_added' in request.POST and 'installed' not in request.GET:
                    installed = request.POST.get('fb_sig_added', False)
                    kt_params = get_kt_params(request)
                    uid = get_uid(request)

                    self.analytics_interface.invite_response(installed=installed,
                                                             tracking_tag=kt_params['u'],
                                                             template_id=kt_params['t'],
                                                             recipient_id=uid,
                                                             subtype_1=kt_params['st1'],
                                                             subtype_2=kt_params['st2'],
                                                             subtype_3=kt_params['st3']).thread_send()
                    if self.redirect:
                        return facebook_redirect(callback_to_facebook(strip_params(request.build_absolute_uri())))

            # Email click
            elif kt_type == "nte":
                if 'kt_ut' in request.GET and 'fb_sig_added' in request.POST:
                    installed = request.POST.get('fb_sig_added', False)
                    kt_params = get_kt_params(request)
                    uid = get_uid(request)
                    
                    self.analytics_interface.email_response(installed=installed,
                                                            tracking_tag=kt_params['u'],
                                                            recipient_id=uid,
                                                            subtype_1=kt_params['st1'],
                                                            subtype_2=kt_params['st2'],
                                                            subtype_3=kt_params['st3']).thread_send()
                    if self.redirect:
                        return facebook_redirect(callback_to_facebook(strip_params(request.build_absolute_uri())))
             
            # UCC
            elif kt_type == "fdp" or \
                   kt_type == "ad" or \
                   kt_type == "prt" or \
                   kt_type == "prf" or \
                   kt_type == "partner" or \
                   kt_type == "profile":
                installed = request.POST.get('fb_sig_added', False)
                kt_params = get_kt_params(request)
                uid = get_uid(request)
                short_tag = generate_short_tag()

                self.analytics_interface.ucc(uid=uid,
                                             type=kt_type,
                                             installed=installed,
                                             short_tracking_tag=short_tag,
                                             subtype_1=kt_params['st1'],
                                             subtype_2=kt_params['st2'],
                                             subtype_3=kt_params['st3']).thread_send()
                if self.redirect:
                    return facebook_redirect(callback_to_facebook(strip_params(request.build_absolute_uri())))
        
