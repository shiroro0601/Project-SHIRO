from company.brain import Brain
from company.core import Job, Workflow
from company.agents.planner_ai import PlannerAI
from company.agents.script_writer_ai import ScriptWriterAI
from company.agents.director_ai import DirectorAI
from company.agents.artist_ai import ArtistAI


if __name__ == "__main__":
    brain = Brain(provider="dummy", model="shiro-local")

    job = Job("猫の意外な雑学")

    workflow = Workflow(name="AI Video Planning Workflow")
    workflow.add_step(PlannerAI(brain=brain))
    workflow.add_step(ScriptWriterAI(brain=brain))
    workflow.add_step(DirectorAI(brain=brain))
    workflow.add_step(ArtistAI(brain=brain))

    result_job = workflow.run(job)

    print("AI社員Workflow統合テスト 完了")
    print("job_id:", result_job.get("job_id"))
    print("status:", result_job.get("status"))
    print("planner:", result_job.get("planner")[:50])
    print("script_writer:", result_job.get("script_writer")[:50])
    print("director:", result_job.get("director")[:50])
    print("artist:", result_job.get("artist")[:50])