from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.agents.requirements_agent import RequirementsAgent
from app.graph.state import create_initial_state
from app.models.domain.enums import AgentType
from app.models.domain.project import (
    FunctionalRequirement,
    NonFunctionalRequirement,
    RequirementsDoc,
    UserStory,
)


class TestRequirementsDocSchema:
    """Test the RequirementsDoc Pydantic schema."""

    def test_valid_requirements_doc(self):
        doc = RequirementsDoc(
            title="Test Project",
            purpose="This is a test project to validate the schema with sufficient detail.",
            scope="In-scope: testing. Out-of-scope: production deployment.",
            functional_requirements=[
                FunctionalRequirement(
                    id="FR-01",
                    description="Users shall be able to register and log in using email and password.",
                    priority="P0",
                ),
                FunctionalRequirement(
                    id="FR-02",
                    description="Users shall be able to create, read, update, and delete their profile information.",
                    priority="P0",
                ),
                FunctionalRequirement(
                    id="FR-03",
                    description="The system shall validate all user input before processing requests.",
                    priority="P0",
                ),
                FunctionalRequirement(
                    id="FR-04",
                    description="Users shall be able to search for items by keyword, category, and price range.",
                    priority="P1",
                ),
                FunctionalRequirement(
                    id="FR-05",
                    description="The system shall paginate search results with a configurable page size.",
                    priority="P1",
                ),
                FunctionalRequirement(
                    id="FR-06",
                    description="Users shall be able to add items to a shopping cart and proceed to checkout.",
                    priority="P0",
                ),
                FunctionalRequirement(
                    id="FR-07",
                    description="The system shall process payments through a third-party payment gateway.",
                    priority="P0",
                ),
                FunctionalRequirement(
                    id="FR-08",
                    description="The system shall send email notifications for order confirmations and status updates.",
                    priority="P1",
                ),
            ],
            non_functional_requirements=[
                NonFunctionalRequirement(
                    id="NFR-01",
                    description="All API responses shall complete within 300ms at the 95th percentile under normal load.",
                    category="performance",
                ),
                NonFunctionalRequirement(
                    id="NFR-02",
                    description="All user passwords shall be hashed using bcrypt with a cost factor of 12.",
                    category="security",
                ),
                NonFunctionalRequirement(
                    id="NFR-03",
                    description="The web interface shall be usable on screens as small as 320px wide.",
                    category="usability",
                ),
                NonFunctionalRequirement(
                    id="NFR-04",
                    description="The system shall maintain 99.9% uptime measured monthly.",
                    category="availability",
                ),
            ],
            user_stories=[
                UserStory(
                    id="US-01",
                    description="As a new user, I want to create an account with my email so that I can access personalized features.",
                    priority="P0",
                ),
                UserStory(
                    id="US-02",
                    description="As a returning user, I want to log in quickly so that I can continue where I left off.",
                    priority="P0",
                ),
                UserStory(
                    id="US-03",
                    description="As an admin, I want to view usage analytics so that I can understand user behavior.",
                    priority="P1",
                ),
            ],
            constraints=["Must use Python 3.12+", "Must deploy on AWS infrastructure"],
            assumptions=["Users have reliable internet access", "Email delivery service is available"],
            open_issues=["Should we support SSO in v1?"],
        )
        assert doc.title == "Test Project"
        assert len(doc.functional_requirements) == 8
        assert len(doc.non_functional_requirements) == 4
        assert len(doc.user_stories) == 3

    def test_fr_id_pattern_validation(self):
        with pytest.raises(ValidationError):
            FunctionalRequirement(id="FR-1", description="Valid description here that is long enough.", priority="P0")

    def test_fr_short_description(self):
        with pytest.raises(ValidationError):
            FunctionalRequirement(id="FR-01", description="Short", priority="P0")

    def test_nfr_invalid_category(self):
        with pytest.raises(ValidationError):
            NonFunctionalRequirement(
                id="NFR-01", description="Valid description that is long enough for the field.", category="invalid"
            )

    def test_us_wrong_id_format(self):
        with pytest.raises(ValidationError):
            UserStory(id="STORY-01", description="As a user, I want to do something so that I benefit.", priority="P0")

    def test_doc_to_dict_roundtrip(self):
        doc = RequirementsDoc(
            title="Test",
            purpose="A test purpose that is long enough to pass validation.",
            scope="The scope is also long enough to pass validation checks easily.",
            functional_requirements=[
                FunctionalRequirement(
                    id="FR-01", description="First functional requirement description.", priority="P0"
                ),
                FunctionalRequirement(
                    id="FR-02", description="Second functional requirement description.", priority="P0"
                ),
                FunctionalRequirement(
                    id="FR-03", description="Third functional requirement description.", priority="P0"
                ),
                FunctionalRequirement(
                    id="FR-04", description="Fourth functional requirement description.", priority="P1"
                ),
                FunctionalRequirement(
                    id="FR-05", description="Fifth functional requirement description.", priority="P1"
                ),
                FunctionalRequirement(
                    id="FR-06", description="Sixth functional requirement description.", priority="P0"
                ),
                FunctionalRequirement(
                    id="FR-07", description="Seventh functional requirement description.", priority="P0"
                ),
                FunctionalRequirement(
                    id="FR-08", description="Eighth functional requirement description.", priority="P1"
                ),
            ],
            non_functional_requirements=[
                NonFunctionalRequirement(
                    id="NFR-01", description="Performance: APIs respond under 300ms.", category="performance"
                ),
                NonFunctionalRequirement(
                    id="NFR-02", description="Security: All data encrypted at rest.", category="security"
                ),
                NonFunctionalRequirement(
                    id="NFR-03", description="Usability: Works on all screen sizes.", category="usability"
                ),
                NonFunctionalRequirement(
                    id="NFR-04", description="Availability: 99.9% uptime SLA.", category="availability"
                ),
            ],
            user_stories=[
                UserStory(
                    id="US-01", description="As a user, I want to login so that I can access my account.", priority="P0"
                ),
                UserStory(
                    id="US-02", description="As a user, I want to search so that I find what I need.", priority="P1"
                ),
                UserStory(
                    id="US-03", description="As an admin, I want reports so that I understand usage.", priority="P1"
                ),
            ],
            constraints=["Constraint 1"],
            assumptions=["Assumption 1"],
        )
        data = doc.model_dump()
        restored = RequirementsDoc.model_validate(data)
        assert restored.title == doc.title
        assert len(restored.functional_requirements) == 8
        assert restored.functional_requirements[0].id == "FR-01"

    def test_doc_frozen(self):
        doc = RequirementsDoc(
            title="Test",
            purpose="A test purpose that is long enough to pass validation.",
            scope="The scope is also long enough to pass validation checks easily.",
            functional_requirements=[
                FunctionalRequirement(
                    id="FR-01", description="First functional requirement description.", priority="P0"
                ),
                FunctionalRequirement(
                    id="FR-02", description="Second functional requirement description.", priority="P0"
                ),
                FunctionalRequirement(
                    id="FR-03", description="Third functional requirement description.", priority="P0"
                ),
                FunctionalRequirement(
                    id="FR-04", description="Fourth functional requirement description.", priority="P1"
                ),
                FunctionalRequirement(
                    id="FR-05", description="Fifth functional requirement description.", priority="P1"
                ),
                FunctionalRequirement(
                    id="FR-06", description="Sixth functional requirement description.", priority="P0"
                ),
                FunctionalRequirement(
                    id="FR-07", description="Seventh functional requirement description.", priority="P0"
                ),
                FunctionalRequirement(
                    id="FR-08", description="Eighth functional requirement description.", priority="P1"
                ),
            ],
            non_functional_requirements=[
                NonFunctionalRequirement(
                    id="NFR-01", description="Performance: APIs respond under 300ms.", category="performance"
                ),
                NonFunctionalRequirement(
                    id="NFR-02", description="Security: All data encrypted at rest.", category="security"
                ),
                NonFunctionalRequirement(
                    id="NFR-03", description="Usability: Works on all screen sizes.", category="usability"
                ),
                NonFunctionalRequirement(
                    id="NFR-04", description="Availability: 99.9% uptime SLA.", category="availability"
                ),
            ],
            user_stories=[
                UserStory(
                    id="US-01", description="As a user, I want to login so that I can access my account.", priority="P0"
                ),
                UserStory(
                    id="US-02", description="As a user, I want to search so that I find what I need.", priority="P1"
                ),
                UserStory(
                    id="US-03", description="As an admin, I want reports so that I understand usage.", priority="P1"
                ),
            ],
            constraints=["C1"],
            assumptions=["A1"],
        )
        with pytest.raises(ValidationError):
            doc.title = "Changed"


class TestRequirementsAgent:
    """Tests for the RequirementsAgent itself."""

    def test_agent_type(self):
        agent = RequirementsAgent(llm_service=None)  # type: ignore
        assert agent.agent_type == AgentType.REQUIREMENTS

    def test_system_prompt_is_string(self):
        agent = RequirementsAgent(llm_service=None)
        prompt = agent.system_prompt
        assert isinstance(prompt, str)
        assert len(prompt) > 500
        assert "Senior Product Manager" in prompt

    def test_output_model_is_requirements_doc(self):
        agent = RequirementsAgent(llm_service=None)
        assert agent.output_model == RequirementsDoc

    def test_state_field(self):
        agent = RequirementsAgent(llm_service=None)
        assert agent._state_field() == "requirements"

    def test_build_user_prompt_includes_idea(self, sample_idea: str):
        agent = RequirementsAgent(llm_service=None)
        state = create_initial_state(idea=sample_idea)
        prompt = agent.build_user_prompt(state)
        assert sample_idea in prompt
        assert "Functional Requirements" in prompt or "functional" in prompt.lower()

    def test_build_user_prompt_includes_constraints(self, sample_idea: str):
        agent = RequirementsAgent(llm_service=None)
        constraints = {"tech_stack": ["python", "fastapi"]}
        state = create_initial_state(idea=sample_idea, constraints=constraints)
        prompt = agent.build_user_prompt(state)
        assert "tech_stack" in prompt

    def test_validate_output_passes_valid_doc(self):
        agent = RequirementsAgent(llm_service=None)
        frs = [
            FunctionalRequirement(
                id=f"FR-{i:02d}",
                description=f"Functional requirement number {i} that is long enough to be valid.",
                priority="P0" if i < 5 else "P1",
            )
            for i in range(1, 11)
        ]
        nfrs = [
            NonFunctionalRequirement(
                id=f"NFR-{i:02d}",
                description=f"Non-functional requirement {i} with enough description to be valid.",
                category=c,
            )
            for i, c in enumerate(["performance", "security", "usability", "reliability", "scalability"], 1)
        ]
        uss = [
            UserStory(
                id=f"US-{i:02d}",
                description=f"As a user, I want feature {i}, so that I can accomplish my goals.",
                priority="P0",
            )
            for i in range(1, 4)
        ]
        doc = RequirementsDoc(
            title="Test Project",
            purpose="A comprehensive test project with enough detail in the purpose field to pass all validations.",
            scope="In scope: testing valid documents. Out of scope: invalid documents.",
            functional_requirements=frs,
            non_functional_requirements=nfrs,
            user_stories=uss,
            constraints=["Must use Python"],
            assumptions=["Internet required"],
            open_issues=["Question here?"],
        )
        # Should not raise
        result = agent._validate_output(doc)
        assert result is doc

    def test_validate_output_rejects_short_frs(self):
        agent = RequirementsAgent(llm_service=None)
        frs = [
            FunctionalRequirement(
                id=f"FR-{i:02d}", description=f"Functional requirement {i} that is long enough to pass.", priority="P0"
            )
            for i in range(1, 6)
        ]
        nfrs = [
            NonFunctionalRequirement(
                id=f"NFR-{i:02d}", description=f"NFR {i} with enough text to be valid here.", category="security"
            )
            for i in range(1, 4)
        ]
        uss = [
            UserStory(id=f"US-{i:02d}", description=f"As a user, I want feature {i} so that I benefit.", priority="P0")
            for i in range(1, 3)
        ]
        doc = RequirementsDoc(
            title="Test",
            purpose="A test purpose that is long enough to pass validation checks here.",
            scope="The scope field must also have enough text to be valid.",
            functional_requirements=frs,
            non_functional_requirements=nfrs,
            user_stories=uss,
            constraints=["C1"],
            assumptions=["A1"],
        )
        with pytest.raises(ValueError, match="Too few functional requirements"):
            agent._validate_output(doc)

    def test_validate_output_rejects_vague_terms(self):
        agent = RequirementsAgent(llm_service=None)
        frs = [
            FunctionalRequirement(
                id=f"FR-{i:02d}",
                description=f"System should be user-friendly and fast for requirement {i}.",
                priority="P0" if i < 4 else "P1",
            )
            for i in range(1, 11)
        ]
        nfrs = [
            NonFunctionalRequirement(
                id=f"NFR-{i:02d}",
                description=f"Non-functional requirement {i} with enough description to be valid.",
                category=c,
            )
            for i, c in enumerate(["performance", "security", "usability", "reliability", "scalability"], 1)
        ]
        uss = [
            UserStory(
                id=f"US-{i:02d}",
                description=f"As a user, I want feature {i} so that I can accomplish my goals.",
                priority="P0",
            )
            for i in range(1, 4)
        ]
        doc = RequirementsDoc(
            title="Test",
            purpose="A test purpose that is long enough to pass validation checks.",
            scope="The scope is also long enough to pass all validation checks.",
            functional_requirements=frs,
            non_functional_requirements=nfrs,
            user_stories=uss,
            constraints=["C1"],
            assumptions=["A1"],
        )
        with pytest.raises(ValueError, match="vague term|user-friendly"):
            agent._validate_output(doc)

    def test_validate_output_rejects_missing_security_nfr(self):
        agent = RequirementsAgent(llm_service=None)
        frs = [
            FunctionalRequirement(
                id=f"FR-{i:02d}",
                description=f"Functional requirement number {i} that is long enough to be valid.",
                priority="P0" if i < 4 else "P1",
            )
            for i in range(1, 11)
        ]
        # Only performance, no security
        nfrs = [
            NonFunctionalRequirement(
                id=f"NFR-{i:02d}",
                description=f"NFR {i} with enough description text to be valid here.",
                category="performance",
            )
            for i in range(1, 5)
        ]
        uss = [
            UserStory(
                id=f"US-{i:02d}",
                description=f"As a user, I want feature {i} so that I can accomplish my goals.",
                priority="P0",
            )
            for i in range(1, 4)
        ]
        doc = RequirementsDoc(
            title="Test",
            purpose="A test purpose that is long enough to pass validation checks.",
            scope="The scope is also long enough to pass all validation checks.",
            functional_requirements=frs,
            non_functional_requirements=nfrs,
            user_stories=uss,
            constraints=["C1"],
            assumptions=["A1"],
        )
        with pytest.raises(ValueError, match="Missing required NFR categories.*security"):
            agent._validate_output(doc)

    def test_validate_output_rejects_bad_us_format(self):
        agent = RequirementsAgent(llm_service=None)
        frs = [
            FunctionalRequirement(
                id=f"FR-{i:02d}",
                description=f"Functional requirement number {i} that is long enough to be valid.",
                priority="P0" if i < 4 else "P1",
            )
            for i in range(1, 11)
        ]
        nfrs = [
            NonFunctionalRequirement(
                id=f"NFR-{i:02d}", description=f"NFR {i} with enough detail to be valid here.", category=c
            )
            for i, c in enumerate(["performance", "security", "usability", "reliability"], 1)
        ]
        # Bad format: missing "so that"
        uss = [
            UserStory(id="US-01", description="User can login to the system.", priority="P0"),
            UserStory(id="US-02", description="User can search items.", priority="P1"),
            UserStory(id="US-03", description="Admin can view reports.", priority="P1"),
        ]
        doc = RequirementsDoc(
            title="Test",
            purpose="A test purpose that is long enough to pass validation checks.",
            scope="The scope is also long enough to pass all validation checks.",
            functional_requirements=frs,
            non_functional_requirements=nfrs,
            user_stories=uss,
            constraints=["C1"],
            assumptions=["A1"],
        )
        with pytest.raises(ValueError, match="does not follow format"):
            agent._validate_output(doc)

    def test_sanitize_output(self):
        agent = RequirementsAgent(llm_service=None)
        doc = RequirementsDoc(
            title="  Test Project  ",
            purpose="  A purpose with spaces  that is long enough to be valid after trimming.  ",
            scope="  A scope with extra whitespace that still passes validation checks.  ",
            functional_requirements=[
                FunctionalRequirement(id="FR-01", description="  Spaces around text  ", priority="P0"),
                FunctionalRequirement(id="FR-02", description="Another requirement description here.", priority="P1"),
                FunctionalRequirement(
                    id="FR-03", description="Third requirement with enough text here.", priority="P1"
                ),
                FunctionalRequirement(
                    id="FR-04", description="Fourth requirement with enough text length.", priority="P0"
                ),
                FunctionalRequirement(
                    id="FR-05", description="Fifth requirement that has enough text here.", priority="P2"
                ),
                FunctionalRequirement(
                    id="FR-06", description="Sixth requirement with a valid description.", priority="P0"
                ),
                FunctionalRequirement(
                    id="FR-07", description="Seventh requirement with a description text.", priority="P1"
                ),
                FunctionalRequirement(
                    id="FR-08", description="Eighth requirement with enough description.", priority="P0"
                ),
                FunctionalRequirement(
                    id="FR-09", description="Ninth requirement that is long enough here.", priority="P1"
                ),
                FunctionalRequirement(
                    id="FR-10", description="Tenth requirement with enough text length.", priority="P0"
                ),
            ],
            non_functional_requirements=[
                NonFunctionalRequirement(id="NFR-01", description="  Performance desc  ", category="performance"),
                NonFunctionalRequirement(
                    id="NFR-02", description="Security description with enough text.", category="security"
                ),
                NonFunctionalRequirement(
                    id="NFR-03", description="Usability: screen reader support.", category="usability"
                ),
                NonFunctionalRequirement(
                    id="NFR-04", description="Reliability: automatic failover.", category="reliability"
                ),
                NonFunctionalRequirement(
                    id="NFR-05", description="Scalability: horizontal scaling.", category="scalability"
                ),
            ],
            user_stories=[
                UserStory(
                    id="US-01",
                    description="  As a user, I want to trim spaces so that the data is clean.  ",
                    priority="P0",
                ),
                UserStory(
                    id="US-02",
                    description="As a user, I want normalized priorities so that validation passes.",
                    priority="P1",
                ),
                UserStory(
                    id="US-03",
                    description="As an admin, I want clean data so that reports are accurate.",
                    priority="P2",
                ),
            ],
            constraints=["  Constraint 1  ", "Constraint 2", "  Constraint 1  "],
            assumptions=["  Assumption 1  ", "Assumption 2", "  Assumption 1  "],
            open_issues=["  Issue 1  "],
        )
        sanitized = agent._sanitize_output(doc)
        assert sanitized.title == "Test Project"
        assert sanitized.functional_requirements[0].description == "Spaces around text"
        assert sanitized.functional_requirements[0].priority == "P0"
        assert sanitized.non_functional_requirements[0].category == "performance"
        assert sanitized.user_stories[0].priority == "P0"
        assert sanitized.constraints == ["Constraint 1", "Constraint 2"]
        assert sanitized.assumptions == ["Assumption 1", "Assumption 2"]

    def test_build_state_updates(self, sample_idea: str):
        agent = RequirementsAgent(llm_service=None)
        state = create_initial_state(idea=sample_idea)
        frs = [
            FunctionalRequirement(
                id=f"FR-{i:02d}",
                description=f"Functional requirement number {i} that is long enough to pass validation.",
                priority="P0",
            )
            for i in range(1, 11)
        ]
        nfrs = [
            NonFunctionalRequirement(
                id=f"NFR-{i:02d}", description=f"NFR {i} with enough description text to pass.", category=c
            )
            for i, c in enumerate(["performance", "security", "usability", "reliability", "scalability"], 1)
        ]
        uss = [
            UserStory(
                id=f"US-{i:02d}",
                description=f"As a user, I want feature {i} so that I can accomplish my goals.",
                priority="P0",
            )
            for i in range(1, 4)
        ]
        output = RequirementsDoc(
            title="Test",
            purpose="A test purpose that is long enough to pass all validation checks here.",
            scope="The scope field also has enough text to pass all validations now.",
            functional_requirements=frs,
            non_functional_requirements=nfrs,
            user_stories=uss,
            constraints=["C1"],
            assumptions=["A1"],
        )
        token_usage = {"prompt_tokens": 100, "completion_tokens": 200, "total_tokens": 300}
        updates = agent._build_state_updates(state, output, token_usage)
        assert "requirements" in updates
        assert updates["current_agent"] == "requirements"
        assert updates["revision"] == 1
        assert "token_usage" in updates
        assert updates["token_usage"][0]["total_tokens"] == 300

    def test_agent_has_retries(self):
        agent = RequirementsAgent(llm_service=None)
        assert agent.max_retries == 2
