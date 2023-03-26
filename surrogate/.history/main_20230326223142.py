from emulator import Emulator
from dataloader import DataGenerator,generate_file
from datetime import datetime
import argparse,yaml
from swmm_api import read_inp_file
from envs import shunqing

def parser(config=None):
    parser = argparse.ArgumentParser(description='surrogate')
    parser.add_argument('--env',type=str,default='shunqing',help='set drainage scenarios')
    parser.add_argument('--conv',type=str,default='GCNconv',help='convolution type')
    parser.add_argument('--embed_size',type=int,default=128,help='number of channels in each convolution layer')
    parser.add_argument('--n_layer',type=int,default=3,help='number of convolution layers')
    parser.add_argument('--activation',type=str,default='relu',help='activation function')
    parser.add_argument('--recurrent',type=str,default='GRU',help='recurrent type')
    parser.add_argument('--hidden_dim',type=int,default=64,help='number of channels in each recurrent layer')
    parser.add_argument('--seq_len',type=int,default=6,help='state sequential length')
    parser.add_argument('--resnet',type=bool,default=True,help='if use resnet')
    parser.add_argument('--loss_function',type=str,default='MeanSquaredError',help='Loss function')
    parser.add_argument('--optimizer',type=str,default='Adam',help='optimizer')
    parser.add_argument('--learning_rate',type=float,default=1e-3,help='learning rate')
    # https://www.cnblogs.com/zxyfrank/p/15414605.html
    given_config,remaining = parser.parse_known_args()
    if config is not None:
        hyps = yaml.load(open(config,'r'),yaml.FullLoader)
        parser.set_defaults(**hyps[given_config.env])
    args = parser.parse_args(remaining)
    print('Training configs: {}'.format(args))
    return args

if __name__ == "__main__":
    
    args = parser('config.yaml')
    
    env = shunqing()

    inp = read_inp_file(env.config['swmm_input'])
    events = generate_file(inp,env.config['rainfall'])
    dG = DataGenerator(env,seq_len=4)
    dG.generate(events,processes=1)

    emul = Emulator(args.conv,args.edges,args.resnet,args.recurrent,args)

