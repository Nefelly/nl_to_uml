from flask import (
    jsonify,
    request
)
from nl2uml.service import (
    NlService
)
from ....response import (
    failure,
    fail,
    success
)


def nl2uml():
    context = request.json.get('context')
    nlservice = NlService(context)
    data, status = nlservice.mainMethod()
    if not status:
        return fail()
    return success(data)


def simple_nl2uml():
    context = request.args.get('context')
    nlservice = NlService(context)
    data, status = nlservice.mainMethod()
    if not status:
        return fail()
    return success(data)
