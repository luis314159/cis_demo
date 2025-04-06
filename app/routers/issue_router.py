from typing import List
from fastapi import APIRouter, status
from sqlmodel import select
from models import Issue, IssueCreate,IssueResponse, IssueUpdate, Process
from db import SessionDep
from fastapi import HTTPException

router = APIRouter(
    prefix="/issue",
    tags=["Issue"]
)


@router.get("/", response_model=List[IssueResponse], status_code=status.HTTP_200_OK)
def read_issues(*, session : SessionDep):
    """
    ## Get all issues

    Retrieves a complete list of all issues registered in the system.

    ### Returns:
    - **List[IssueResponse]**: List of issue objects containing:
        - issue_id: Unique identifier of the issue
        - issue_description: Description of the issue

    ### Example Response:
    ```json
    [
        {
            "issue_id": 1,
            "issue_description": "Issue description 1"
        },
        {
            "issue_id": 2,
            "issue_description": "Issue description 2"
        }
    ]
    ```
    """
    issues = session.exec(select(Issue)).all()
    return issues

@router.get("/{issue_id}", response_model=IssueResponse, status_code=status.HTTP_200_OK)
def read_issue(*, issue_id: int, session : SessionDep):
    """
    ## Get issue by ID

    Retrieves a single issue based on the provided issue ID.

    ### Parameters:
    - **issue_id** (*int*): Unique identifier of the issue to retrieve.

    ### Returns:
    - **IssueResponse**: Issue object containing:
        - issue_id: Unique identifier of the issue
        - issue_description: Description of the issue

    ### Example Response:
    ```json
    {
        "issue_id": 1,
        "issue_description": "Issue description 1"
    }
    ```
    """
    issue = session .get(Issue, issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    return issue

@router.post("/", response_model=IssueResponse, status_code=status.HTTP_201_CREATED)
def create_issue(*, session: SessionDep, issue: IssueCreate):
    """
    ## Create issue

    Creates a new issue in the system and associates it with a process.

    ### Request Body:
    - **IssueCreate**: Object containing:
        - issue_description: Description of the new issue (cannot be empty).
        - process_id: Identifier of the process to associate with the issue.

    ### Validation:
    - Ensures that the issue_description is not empty.
    - Verifies that a process with the provided process_id exists.

    ### Returns:
    - **IssueResponse**: The newly created issue object containing:
        - issue_id: Unique identifier of the newly created issue.
        - issue_description: Description of the issue.
        - process_id: Identifier of the associated process.

    ### Example Request:
    ```json
    {
        "issue_description": "New issue description",
        "process_id": 2
    }
    ```

    ### Example Response:
    ```json
    {
        "issue_id": 3,
        "issue_description": "New issue description",
        "process_id": 2
    }
    ```
    """
    # Validate issue_description if needed (e.g., not empty)
    if not issue.issue_description.strip():
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Issue description cannot be empty")
    
    existing_issue = session.exec(select(Issue).where(Issue.issue_description == issue.issue_description)).first()
    if existing_issue :
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Issue description already exists")

    
    # Verify that the process exists
    db_process = session.get(Process, issue.process_id)
    if not db_process:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Process not found")
    
    db_issue = Issue(
        issue_description=issue.issue_description,
        process_id=issue.process_id
    )
    session.add(db_issue)
    session.commit()
    session.refresh(db_issue)
    return db_issue

@router.put("/{issue_id}", response_model=IssueResponse, status_code=status.HTTP_200_OK)
def update_issue(*, session: SessionDep, issue_id: int, issue: IssueUpdate):
    """
    ## Update issue

    Updates an existing issue with the provided data.

    ### Parameters:
    - **issue_id** (*int*): Unique identifier of the issue to update.
    - **IssueUpdate**: Object containing updated issue data:
        - issue_description: (Optional) Updated description of the issue.
        - process_id: (Optional) Identifier of the process to associate with the issue.

    ### Validation:
    - Validates that if an updated issue_description is provided, it is not empty.
    - If a new process_id is provided, verifies that the corresponding Process exists.

    ### Returns:
    - **IssueResponse**: The updated issue object containing:
        - issue_id: Unique identifier of the issue.
        - issue_description: Updated description of the issue.
        - process_id: Associated process identifier.

    ### Example Request:
    ```json
    {
        "issue_description": "Updated issue description",
        "process_id": 2
    }
    ```

    ### Example Response:
    ```json
    {
        "issue_id": 1,
        "issue_description": "Updated issue description",
        "process_id": 2
    }
    ```
    """
    db_issue = session.get(Issue, issue_id)
    if not db_issue:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Issue not found")

    update_data = issue.model_dump(exclude_unset=True)

    # Validate issue_description if provided
    if "issue_description" in update_data and not update_data["issue_description"].strip():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Issue description cannot be empty")
    
    # Verify that the process exists if process_id is provided
    if "process_id" in update_data:
        db_process = session.get(Process, update_data["process_id"])
        if not db_process:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Process not found")

    for key, value in update_data.items():
        setattr(db_issue, key, value)

    session.add(db_issue)
    session.commit()
    session.refresh(db_issue)
    return db_issue

@router.delete("/{issue_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_issue(*, issue_id: int, session : SessionDep):
    """
    ## Delete issue

    Deletes an existing issue from the system based on the provided issue ID.

    ### Parameters:
    - **issue_id** (*int*): Unique identifier of the issue to delete.

    ### Returns:
    - **None**

    ### Example Response:
    HTTP 204 No Content
    """
    db_issue = session .get(Issue, issue_id)
    if not db_issue:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Issue not found")
    
    session .delete(db_issue)
    session .commit()
    return None