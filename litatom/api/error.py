# encoding=utf-8
Success = {'success': True, 'result': 0}

Failed = {'success': False, 'result': -1}
FailedVersion = {'success': False, 'result': -9, 'msg': u'版本过低，请升级到最新版本'}
FailedLackOfField = {'success': False, 'result': -2, 'msg': u'lake of field'}
FailedSession = {'success': False, 'result': -10, 'msg': u'login time out, please relogin'}
FailedNotEnoughDiamonds = {'success': False, 'result': -13, 'msg': u'not enough diamonds, please deposit first.'}
FailedFinishedSession = {'success': False, 'result': -11, 'msg': u'need to complete your profile; finish it first~'}
FailedNotAdmin = {'success': False, 'result': -12, 'msg': u'you are not admin'}
FailedNotTimesLeft = {'success': False, 'result': -13, 'msg': u'Your match opportunity has run out, please try again tomorrow'}
