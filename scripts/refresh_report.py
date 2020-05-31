from litatom.model import Report

def run():
    reports = Report.objects(create_ts__gte=1589904000,dealed=False)
    for report in reports:
        if report.reason == 'match':
            report.forbid_weight = 2
        else:
            report.forbid_weight = 4
        report.save()

if __name__ == '__main__':
    run()