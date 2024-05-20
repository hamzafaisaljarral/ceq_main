from flask_restful import Api
from ceq_user.user.auth import CEQLoginApi
from ceq_user.user.view import CEQAddUserAPI, CEQAddNewUserAPI, CEQUpdateUserAPI, \
    CEQViewAllUserAPI, CEQDeleteUserAPI, CEQUpdateUserStatusAPI, SearchUsers, TechnicianFileUpload
from consumer.view import Test, CreateConsumerAudit, GetConsumerAudit, GetConsumerAuditList,\
    DeleteConsumerAudit, UpdateConsumerAudit, AddErrorCategory, GetAllCategories, DeleteConsumerImage,\
    AllTeams, TechnicianDetails, AddTechnician, UpdateTechnician, DeleteTechnician, SearchTechnicians,\
    UploadCSV, ExportCSV    
from business.view import CreateBusinessAudit, BusinessAuditDetails, GetBusinessAuditList,\
    DeleteBusinessAudit, UpdateBusinessAudit, AssignAudit, BusinessAuditors, UploadExcelBusinessAudit, BusinessAuditDownload
    
from over_view.view import AuditDashboardQuarter, AuditDashboardMonth, OverViewReport
from consumer.report_view import RegionComplianceReport, RegionComplianceReportGraph, RegionComplianceReportSharedZone, \
    RegionNonComplianceTopContributor, SharedzoneNonComplianceTopContributor, OtherNonComplianceTopContributor, \
    CategoryNonComplianceContributor, AuditedTechnicians, ComplianceandNonComplianceImages



def initialize_routes(app):
    api = Api(app)

    # user management path
    api.add_resource(CEQLoginApi, '/ceq/user/login')
    api.add_resource(CEQViewAllUserAPI, '/ceq/user/view/all')
    api.add_resource(CEQAddUserAPI, '/ceq/user/add')
    api.add_resource(CEQAddNewUserAPI, '/ceq/new/user/add')
    api.add_resource(CEQUpdateUserAPI, '/ceq/user/update')
    api.add_resource(CEQUpdateUserStatusAPI, '/ceq/user/update/status')
    api.add_resource(CEQDeleteUserAPI, '/ceq/user/delete')
    api.add_resource(SearchUsers, '/ceq/user/search_user') 
    api.add_resource(TechnicianFileUpload, '/ceq/user/technisians_file_upload')
     

  # consumer module path
    api.add_resource(Test, '/ceq/consumer/test')
    api.add_resource(CreateConsumerAudit, '/ceq/consumer/create_audit')
    api.add_resource(GetConsumerAudit, '/ceq/consumer/get_audit')
    api.add_resource(GetConsumerAuditList, '/ceq/consumer/get_audit_list')
    api.add_resource(DeleteConsumerAudit, '/ceq/consumer/delete_audit')
    api.add_resource(UpdateConsumerAudit, '/ceq/consumer/update_audit')
    api.add_resource(DeleteConsumerImage, '/ceq/consumer/delete_image')
    api.add_resource(UploadCSV, '/ceq/consumer/upload_csv')
    api.add_resource(ExportCSV, '/ceq/consumer/export_csv')    
    api.add_resource(AllTeams, '/ceq/consumer/all_teams')
    api.add_resource(AddErrorCategory, '/ceq/add/category')
    api.add_resource(GetAllCategories, '/ceq/get/category')
    api.add_resource(TechnicianDetails, '/ceq/technician/details')
    api.add_resource(AddTechnician, '/ceq/technician/add')
    api.add_resource(UpdateTechnician, '/ceq/technician/update')
    api.add_resource(DeleteTechnician, '/ceq/technician/delete')
    api.add_resource(SearchTechnicians, '/ceq/technician/search')
    
    


    # business module path
    api.add_resource(CreateBusinessAudit, '/ceq/business/create_audit')
    api.add_resource(BusinessAuditDetails, '/ceq/business/get_audit_details')
    api.add_resource(GetBusinessAuditList, '/ceq/business/get_audit_list/')
    api.add_resource(DeleteBusinessAudit, '/ceq/business/delete_audit')
    api.add_resource(UpdateBusinessAudit, '/ceq/business/update_audit')
    api.add_resource(AssignAudit, '/ceq/business/assign_audit')
    api.add_resource(BusinessAuditors, '/ceq/business/all_auditors')
    api.add_resource(UploadExcelBusinessAudit, '/ceq/business/upload_excel')
    api.add_resource(BusinessAuditDownload, '/ceq/business/download_csv')
    
    # over_view module path
    api.add_resource(AuditDashboardMonth, '/ceq/over_view/month_report')
    api.add_resource(OverViewReport, '/ceq/over_view/report')
    api.add_resource(AuditDashboardQuarter, '/ceq/over_view/quarter_report')

    #report compliance
    api.add_resource(RegionComplianceReport, '/ceq/report/region/complaince')
    api.add_resource(RegionComplianceReportGraph, '/ceq/report/region/complaince/graph')
    api.add_resource(RegionComplianceReportSharedZone, '/ceq/report/region/complaince/sharedzone')
    api.add_resource(RegionNonComplianceTopContributor, '/ceq/report/region/non-complaince/top-contributor')
    api.add_resource(SharedzoneNonComplianceTopContributor, '/ceq/report/region/non-complaince/shared_zone')
    api.add_resource(OtherNonComplianceTopContributor, '/ceq/report/region/non-complaince/others')
    api.add_resource(CategoryNonComplianceContributor, '/ceq/report/region/non-complaince/contributor')
    api.add_resource(AuditedTechnicians, '/ceq/report/region/technician/audits')
    api.add_resource(ComplianceandNonComplianceImages, '/ceq/report/region/images/audits')

    