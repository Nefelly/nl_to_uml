# coding: utf-8
"""
测试
"""
import logging

from ...decorator import (
    session_required,
    session_finished_required
)

from ....response import (
    fail,
    success
)

logger = logging.getLogger(__name__)
from flask import (
    jsonify,
    request,
    current_app,
    render_template,
    redirect,
    make_response
)

from ....service import (
    PalmService,
    GlobalizationService,
    ShareStatService,
    UserService
)

logger = logging.getLogger(__name__)


def palm_query():
    pic = request.args.get('pic', '')
    if not pic:
        return fail('don\'t have a palm')
    data, status = PalmService.output_res(pic)
    if status:
        return success(data)
    return fail(data)


@session_finished_required
def times_left():
    return success({'times_left': PalmService.times_left(request.user_id)})


def user_share(share_user_id):
    loc = GlobalizationService.loc_by_uid(share_user_id)
    url = '/api/sns/v1/lit/activity/share_static?loc=' + loc
    ShareStatService.add_stat_item(share_user_id, request.ip)
    return redirect(url)


def getImageMeta(loc='EN'):
    url = 'http://www.litatom.com/api/sns/v1/lit/image/'
    if loc == 'TH':
        return url + '853da5b2-52c4-11ea-9e89-00163e02deb4'
    elif loc == 'VN':
        return url + '964729c8-52c4-11ea-9e89-00163e02deb4'
    else:
        return url + '76925d0a-52c4-11ea-9e89-00163e02deb4'


def getDesMeta(loc='EN'):
    if loc == 'TH':
        return 'ฉันได้รู้จักเพื่อนใหม่5คน'
    elif loc == 'VN':
        return 'Tôi đã gặp được 5 người bạn mới ở Litmatch'
    else:
        return "I met 5 new friends on Litmatch"


def share_static():
    loc = request.args.get('loc')
    r = make_response(
        render_template("litShare.html", ogUrl='http://test.litatom.com/api/sns/v1/lit/activity/share_static',
                        ogImage=getImageMeta(loc), ogDescription=getDesMeta(loc)))
    r.headers.set('Content-Type', 'text/html; charset=utf-8')
    # return current_app.send_static_file('share_index.html'), 200, {'Content-Type': 'text/html; charset=utf-8'}
    return r


@session_required
def claim_rewards():
    data, status = ShareStatService.claim_rewards(request.user_id)
    if status:
        return success()
    return fail(data)


@session_required
def share_num():
    data = ShareStatService.get_shown_num(request.user_id)
    return success(data)


def share_info():
    result_id = request.values.get('result_id')
    analys_results = PalmService.get_res_by_result_id(result_id)
    res = []
    for _ in PalmService.ORDER:
        if analys_results.get(_):
            res.append(analys_results[_])
    return render_template('share_paml.html', analys_result=res,
                           introduce=GlobalizationService.get_region_word('app_introduce')), 200, {
               'Content-Type': 'text/html; charset=utf-8'}
