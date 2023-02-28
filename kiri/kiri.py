import argparse
import toml
from git import Repo
import os
from ruamel.yaml import YAML
import gitlab

if __name__ == "__main__":
    yaml = YAML(typ="rt")
    yaml.preserve_quotes = True
    yaml.default_flow_style = False
    print("Hi!")
    parser = argparse.ArgumentParser(
        prog="ProgramName",
        description="What the program does",
        epilog="Text at the bottom of help",
    )
    parser.add_argument("-f", "--filename", default="kiri.toml", required=False)
    parser.add_argument("-e", "--environment", required=True)
    parser.add_argument("-t", "--tag", required=True)
    parser.add_argument("-i", "--image-name", required=True)
    args = parser.parse_args()
    with open(args.filename, "r") as f:
        config = toml.load(f)
    print(config)

    infra_repo_path = os.path.join(os.getcwd(), "infra_repo")
    infra_repo = Repo.clone_from(
        config["global"]["infrastructure_repository"],
        infra_repo_path,
    )

    kustomization_path = os.path.join(
        infra_repo_path, config["environments"][args.environment]["kustomization_path"]
    )

    with open(kustomization_path, "r") as f:
        kustomization = yaml.load(f)
    print(kustomization)

    for image in filter(
        lambda image: image["name"] == args.image_name, kustomization["images"]
    ):
        image["newTag"] = args.tag

    print(kustomization)

    with open(kustomization_path, "w") as f:
        yaml.dump(kustomization, f)

    upgrade_branch = f"kiri/{config['global']['application_name']}-{args.tag}"

    infra_repo.head.reference = infra_repo.create_head(upgrade_branch)

    infra_repo.index.add(kustomization_path)
    # Provide a commit message
    infra_repo.index.commit(f"Upgrade {args.image_name} to {args.tag}")
    push_status = infra_repo.remotes.origin.push()
    print(push_status)

    gl = gitlab.Gitlab(private_token="")

    project_name_with_namespace = "namespace/project_name"
    project = gl.projects.get(project_name_with_namespace)

    mr = project.mergerequests.create(
        {
            "source_branch": upgrade_branch,
            "target_branch": "master",
            "title": "merge cool feature",
            "labels": ["kiri"],
        }
    )

    mr.merge()
