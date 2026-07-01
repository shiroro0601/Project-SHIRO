from company.core import Employee


class ArtistAI(Employee):
    def __init__(self, brain=None):
        super().__init__(
            name="ArtistAI",
            role="Artist",
            brain=brain
        )

    def create_image_prompts(self, direction: str) -> str:
        prompt = self._build_prompt(direction)
        return self.think(prompt)

    def run(self, job):
        self.log(job, "画像生成プロンプト作成を開始します。")

        direction = job.get("director", "")
        image_prompts = self.create_image_prompts(direction)

        self.update_job(job, "artist", image_prompts)
        self.log(job, "画像生成プロンプト作成を完了しました。")

        return job

    def _build_prompt(self, direction: str) -> str:
        return f"""
あなたはProject SHIROの画像生成担当Artistです。

以下の映像演出指示をもとに、Stable Diffusion用の画像生成プロンプトを作成してください。

映像演出指示:
{direction}

出力内容:
1. 全体の画風
2. シーン1のpositive prompt
3. シーン1のnegative prompt
4. シーン2のpositive prompt
5. シーン2のnegative prompt
6. シーン3のpositive prompt
7. シーン3のnegative prompt
8. シーン4のpositive prompt
9. シーン4のnegative prompt
10. シーン5のpositive prompt
11. シーン5のnegative prompt

条件:
・Stable Diffusionで使いやすい英語プロンプトにする
・各シーンは1枚絵として成立させる
・高品質なアニメ調
・縦長動画向け
・キャラクターの破綻を避ける
・背景を具体的に書く
・negative promptには低品質・崩れ・余分な指などを入れる
・日本語の説明も少し添える
"""


if __name__ == "__main__":
    from company.core import Job
    from company.agents.planner_ai import PlannerAI
    from company.agents.script_writer_ai import ScriptWriterAI
    from company.agents.director_ai import DirectorAI

    job = Job("猫の意外な雑学")

    planner = PlannerAI()
    job = planner.run(job)

    writer = ScriptWriterAI()
    job = writer.run(job)

    director = DirectorAI()
    job = director.run(job)

    artist = ArtistAI()
    result_job = artist.run(job)

    print("ArtistAI Employee対応テスト完了")
    print("artist:", result_job.get("artist")[:50])