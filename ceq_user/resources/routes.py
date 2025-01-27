from flask_restful import Api
from ceq_user.user.auth import CEQLoginApi, CEQLoginApi1, VerifyOTP, LogoutApi
from ceq_user.user.view import CEQAddUserAPI, CEQAddNewUserAPI, CEQUpdateUserAPI, \
    CEQViewAllUserAPI, CEQDeleteUserAPI, CEQUpdateUserStatusAPI, SearchUsers, TechnicianFileUpload
from consumer.view import Test, CreateConsumerAudit, GetConsumerAudit, GetConsumerAuditList,\
    DeleteConsumerAudit, UpdateConsumerAudit, AddErrorCategory, GetAllCategories, DeleteConsumerImage,\
    AllTeams, TechnicianDetails, AddTechnician, UpdateTechnician, DeleteTechnician, SearchTechnicians,\
    UploadCSV, ExportCSV    
from business.view import CreateBusinessAudit, BusinessAuditDetails, GetBusinessAuditList,\
    DeleteBusinessAudit, UpdateBusinessAudit, AssignAudit, BusinessAuditors, UploadExcelBusinessAudit, BusinessAuditDownload
from over_view.view import AuditDashboardQuarter, AuditDashboardYear, OverViewReport,AuditDashboard4Months
from consumer.report_view import RegionComplianceReport, RegionComplianceReportGraph, RegionComplianceReportSharedZone, \
    RegionNonComplianceTopContributor, SharedzoneNonComplianceTopContributor, OtherNonComplianceTopContributor, \
    CategoryNonComplianceContributor, AuditedTechnicians, ComplianceandNonComplianceImages, NonComplianceCategoryLastSixMonths
<<<<<<< HEAD
from business.report_view import RegionComplianceBusinessReport, CategoryBusinessReport, OverallBusinessReport, \
    AccountCategory, RegionWisePastData, NonComplianceContributerSixMonths, NonComplianceContributerVistor, \
    BusinessComplianceandNonComplianceImages 
from fdh.fdh_view import CreateFdh, FdhDetails, FdhList, DeleteFdh, UpdateFdh, DeleteImage, GetFdhVisits,\
    GetFdhViolations, DeleteVisit, FdhMap
=======

from business.report_view import RegionComplianceBusinessReport, CategoryBusinessReport, OverallBusinessReport, \
    AccountCategory, RegionWisePastData, NonComplianceContributerSixMonths, NonComplianceContributerVistor, \
    BusinessComplianceandNonComplianceImages
>>>>>>> refs/remotes/origin/main



def initialize_routes(app):
    api = Api(app)
    # user management path
    api.add_resource(CEQLoginApi, '/ceq/user/login')
    api.add_resource(CEQLoginApi1, '/ceq/user/login1')
    api.add_resource(LogoutApi, '/ceq/user/logout')
    api.add_resource(CEQViewAllUserAPI, '/ceq/user/view/all')
    api.add_resource(CEQAddUserAPI, '/ceq/user/add')
    api.add_resource(CEQAddNewUserAPI, '/ceq/new/user/add')
    api.add_resource(CEQUpdateUserAPI, '/ceq/user/update')
    api.add_resource(CEQUpdateUserStatusAPI, '/ceq/user/update/status')
    api.add_resource(CEQDeleteUserAPI, '/ceq/user/delete')
    api.add_resource(SearchUsers, '/ceq/user/search_user') 
    api.add_resource(TechnicianFileUpload, '/ceq/user/technisians_file_upload')
    api.add_resource(VerifyOTP, '/ceq/user/verify_otp')
    
    

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
    api.add_resource(AuditDashboardYear, '/ceq/over_view/yearly_report')
    api.add_resource(OverViewReport, '/ceq/over_view/report')
    api.add_resource(AuditDashboardQuarter, '/ceq/over_view/quarter_report')
    api.add_resource(AuditDashboard4Months, '/ceq/over_view/4months_report')
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
    api.add_resource(NonComplianceCategoryLastSixMonths, '/ceq/report/region/non-complaince/category')
<<<<<<< HEAD
=======


>>>>>>> refs/remotes/origin/main
    #report business compliance and non compliance
    api.add_resource(RegionComplianceBusinessReport, '/ceq/business/report/region')
    api.add_resource(CategoryBusinessReport, '/ceq/business/report/category')
    api.add_resource(OverallBusinessReport, '/ceq/business/report/overall')
    api.add_resource(AccountCategory, '/ceq/business/account/category')
    api.add_resource(RegionWisePastData,'/ceq/business/account/region')
    api.add_resource(NonComplianceContributerSixMonths, '/ceq/business/non-compliance/months')
    api.add_resource(NonComplianceContributerVistor, '/ceq/business/non-compliance/companies')
    api.add_resource(BusinessComplianceandNonComplianceImages, '/ceq/business/images')
<<<<<<< HEAD
    
    #FDH Module path
    api.add_resource(CreateFdh, '/ceq/fdh/create')
    api.add_resource(FdhDetails, '/ceq/fdh/details')
    api.add_resource(FdhList, '/ceq/fdh/fdhlist')
    api.add_resource(DeleteFdh, '/ceq/fdh/delete')
    api.add_resource(UpdateFdh, '/ceq/fdh/update')
    api.add_resource(DeleteImage, '/ceq/fdh/delete_image')
    api.add_resource(GetFdhVisits, '/ceq/fdh/visiters')
    api.add_resource(GetFdhViolations, '/ceq/fdh/violations')
    api.add_resource(DeleteVisit,'/ceq/fdh/delete_visiter')
    api.add_resource(FdhMap,'/ceq/fdh/maps')
    
    
    
    
    
    
    
    
    
    
=======
>>>>>>> refs/remotes/origin/main

    