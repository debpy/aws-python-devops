Please Follow the below steps to provision the ECS Cluster under the Application Load Balancer.
Step 1: Provision EC2 server / use your own python IDE
Step 2: Attach the IAM role into your EC2 machine (or) configure the Access and Secret key in your machine to use the AWS account.
Step 3: Intall the Python3 and Pip3 in your machine.
Step 4: make sure to copy this "mcp.zip" inside your machine.
Step 5: extract the zipped folder
Step 6: run the following commands ($ pip3 install requirements.txt)
Step 7: run the menu.py file ($ python3 menu.py)
Step 8: Select the option as "B/b" to create new ECR repo and upload your customised nginx webserver image.
Step 9: Select the option as "C/c" to create the complete setup inside your account.
Step 10: Now, we can access the Webserver using the LoadBalancer DNS name.
Step 11: If you want, you can update the service with updated image.Once image updated, first use the option "b/B" and then use the option as "C/c" to update the ECS Service.
Step 12: Once everything is tested, then select the option as "D/d" to destroy the complete setup.
Please follow the above step and execute the scripts.
Note: Incase any error occured, please reach me at "730517@cognizant.com"
