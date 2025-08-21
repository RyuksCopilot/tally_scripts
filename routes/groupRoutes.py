from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.groupService import TallyGroupService

router = APIRouter()

class GroupRequest(BaseModel):
    tally_url: str
    company_name: str
    group_name: str
    parent_group: str | None = None  

@router.post("/create-group")
def create_group(request: GroupRequest):
    try:
        group_manager = TallyGroupService(request.tally_url)
        data = {
            "company_name": request.company_name,
            "group_name": request.group_name,
            "parent_group": request.parent_group,
        }

        result = group_manager.create_group(data)
        return {"message": "Group created successfully", "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# class DeleteGroupRequest(BaseModel):
#     tally_url: str
#     company_name: str
#     group_name: str

# @router.delete("/delete-group")
# def delete_group(request: DeleteGroupRequest):
#     try:
#         group_manager = TallyGroupService(request.tally_url)
#         result = group_manager.delete_group(
#             company_name=request.company_name,
#             group_name=request.group_name
#         )
#         return {"message": "Group deleted successfully", "data": result}
#     except ValueError as e:
#         raise HTTPException(status_code=400, detail=str(e))
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))