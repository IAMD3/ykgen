#for testing agents' function
from kgen import VideoAgent

agent = VideoAgent();

type(agent)

rst =agent.generate("write a hello world story")

print(rst)