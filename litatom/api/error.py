# encoding=utf-8
Success = {'success': True, 'result': 0}

Failed = {'success': False, 'result': -1}
FailedVersion = {'success': False, 'result': -9, 'msg': u'版本过低，请升级到最新版本'}
FailedLackOfField = {'success': False, 'result': -2, 'msg': u'缺少必填字段哦'}
FailedSession = {'success': False, 'result': -10, 'msg': u'登录已过期, 请重新登录'}
FailedFinishedSession = {'success': False, 'result': -11, 'msg': u'需要完善信息, 请先完善个人信息'}
