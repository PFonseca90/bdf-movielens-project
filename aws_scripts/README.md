# AWS Setup

To replicate the project on AWS, we prepared a number of scripts. These scripts were executed in `AWS CloudShell` with the exception of `tmdb_to_s3.sh` which was executed on EC2 because it runs a Python script to process the REST API provided by TMDB.

| Source       | Platform            | Script                   |
|--------------|---------------------|--------------------------|
| Bucket Setup | AWS CloudShell      | make_buckets.sh          |
| MovieLens    | AWS CloudShell      | movielens_32m_to_s3.sh   |
| IMDB         | AWS CloudShell      | imdb_to_s3.sh            |
| TMDB         | EC2                 | tmdb_to_s3/tmdb_fetch.py |


## Running TMDB on EC2

```sh
sudo dnf install -y python3-pip tmux && pip3 install --user requests
aws ssm put-parameter --name /tmdb/token --type SecureString --value '<TMDB read access token>'   # from secret manager.
tmux                                   # keeps the job running if your session drops
bash tmdb_to_s3.sh
```
