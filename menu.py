import sys
from ecs_cluster import launch_ecs_cluster, ecs_service_update
from destroy_setup import destroy_ecs_cluster
from dockerimage import docker_image_push

USER_CHOICE = """
Enter
- 'b' to build and push the new image to ECR
- 'c' to Create a ECS & ALB Setup
- 'd' to Destroy a ECS & ALB Setup
- 'u' to update the ECS Services with new docker image
- 'q' to quit

NOTE: "Before creating anything for the first time, please run the destroy option and new image creation options"

Your Choice: """


def menu():
    user_input = input(USER_CHOICE)
    if (user_input == 'c') or (user_input == 'C'):
        launch_ecs_cluster()
    elif (user_input == 'd') or (user_input == 'D'):
        destroy_ecs_cluster()
    elif (user_input == 'b') or (user_input == 'B'):
        docker_image_push()
    elif (user_input == 'u') or (user_input == 'U'):
        ecs_service_update()
    elif (user_input == 'q') or (user_input == 'Q'):
        print("Thanks for running the Python script")
        sys.exit(2)
    else:
        print("Invalid Option. Please rerun the script")
        sys.exit(2)


menu()
