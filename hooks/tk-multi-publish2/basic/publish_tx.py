"""Submit published Substance EXRs to Royal Render for TX generation."""

import os
import sys

import sgtk
from sgtk.util.filesystem import ensure_folder_exists


HookBaseClass = sgtk.get_hook_baseclass()
RR_ROOT = r"\\alpha\globalava\globals\royalrender"


class SubstancePainterTxPublishPlugin(HookBaseClass):
    @property
    def name(self):
        return "Generate TX via Farm"

    @property
    def description(self):
        return (
            "Optionally submits the published EXRs to Royal Render for TX "
            "generation."
        )

    @property
    def item_filters(self):
        return ["substancepainter.textures"]

    @property
    def settings(self):
        return {}

    def accept(self, settings, item):
        return {"accepted": True, "checked": True}

    def validate(self, settings, item):
        return True

    def publish(self, settings, item):
        publish_path = item.properties.get("sg_publish_path")
        if not publish_path:
            raise Exception(
                "TX generation requires the texture-folder publish task to complete first."
            )

        publish_path = sgtk.util.ShotgunPath.normalize(publish_path)
        sources = sorted(
            (
                os.path.join(publish_path, name)
                for name in os.listdir(publish_path)
                if name.lower().endswith(".exr")
                and os.path.isfile(os.path.join(publish_path, name))
            ),
            key=lambda path: path.lower(),
        )
        if not sources:
            raise Exception("No published EXRs found in '{}'".format(publish_path))

        tx_dir = os.path.join(publish_path, "_tx")
        ensure_folder_exists(tx_dir)
        if any(name.lower().endswith(".tx") for name in os.listdir(tx_dir)):
            raise Exception("Refusing to overwrite existing TX files in '{}'".format(tx_dir))

        job_id_str = self._submit_rr_job(publish_path, sources)
        self.logger.info(
            "Submitted TXGen job {} for {} EXR(s) in '{}'.".format(
                job_id_str, len(sources), publish_path
            )
        )

    def finalize(self, settings, item):
        pass

    def _submit_rr_job(self, publish_path, sources):
        sdk_dir = os.path.join(RR_ROOT, "SDK", "External", "Python")
        if sdk_dir not in sys.path:
            sys.path.insert(0, sdk_dir)
        os.environ["RR_ROOT"] = RR_ROOT

        from rr_python_utils.load_rrsubmit import rrSubmitLib
        import rrJob

        submitter = rrSubmitLib.Submitter()

        app = rrJob._RenderAppBasic()
        app.clear()
        app.name = "TXGen"
        app.rendererName = "Folder"
        app.setVersionBoth("1.0")

        job = rrSubmitLib.createEmptyJob2(sources[0], "TXGen distributed folder 1.0")
        job.renderApp = app
        job.customSceneName = "TXGen DISTRIBUTED - {}".format(
            os.path.basename(publish_path)
        )
        job.layer = "One EXR per RR frame"
        job.seqStart = 1
        job.seqEnd = len(sources)
        job.seqStep = 1
        job.imageFileName = os.path.join(
            publish_path, "_tx", "TXGen_RR_frame.####.tx"
        )
        job.customSet_Str("rrEnvList", "TXGEN_FOLDER=" + publish_path + "~~~")

        job.customDataAppend_Str(
            "rrSubmitterParameter",
            " SequenceDivide=1~1 SeqDivMin=1~1 SeqDivMax=1~1",
        )

        submitter.addJob(job)
        if not submitter.submitJobs():
            raise Exception("Royal Render rejected the TXGen submission.")

        job_id = submitter.jobsSendID(0)
        return rrJob.jID2Str(job_id)
