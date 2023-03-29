from emulator import Emulator
from dataloader import DataGenerator,generate_file
import argparse,yaml,random
from envs import get_env

def parser(config=None):
    parser = argparse.ArgumentParser(description='surrogate')
    parser.add_argument('--env',type=str,default='shunqing',help='set drainage scenarios')
    parser.add_argument('--simulate',action="store_true",help='if simulate rainfall events for training data')
    parser.add_argument('--data_dir',type=str,default='./envs/data/shunqing/',help='the sampling data file')
    parser.add_argument('--ratio',type=float,default=0.8,help='ratio of training events')
    parser.add_argument('--processes',type=int,default=1,help='number of simulation processes')
    parser.add_argument('--act',action="store_true",help='if the environment contains control actions')
    # TODO: if no convolution or recurrent, what argument should be?
    parser.add_argument('--conv',type=str,default='GCNconv',help='convolution type')
    parser.add_argument('--embed_size',type=int,default=128,help='number of channels in each convolution layer')
    parser.add_argument('--n_layer',type=int,default=3,help='number of convolution layers')
    parser.add_argument('--activation',type=str,default='relu',help='activation function')
    parser.add_argument('--recurrent',type=str,default='GRU',help='recurrent type')
    parser.add_argument('--hidden_dim',type=int,default=64,help='number of channels in each recurrent layer')
    parser.add_argument('--seq_len',type=int,default=6,help='state sequential length')
    parser.add_argument('--resnet',action='store_true',help='if use resnet')
    parser.add_argument('--loss_function',type=str,default='MeanSquaredError',help='Loss function')
    parser.add_argument('--optimizer',type=str,default='Adam',help='optimizer')
    parser.add_argument('--learning_rate',type=float,default=1e-3,help='learning rate')
    parser.add_argument('--epochs',type=int,default=100,help='training epochs')
    parser.add_argument('--batch_size',type=int,default=256,help='training batch size')
    # https://www.cnblogs.com/zxyfrank/p/15414605.html
    given_config,_ = parser.parse_known_args()
    if config is not None:
        hyps = yaml.load(open(config,'r'),yaml.FullLoader)
        parser.set_defaults(**hyps[given_config.env])
    args = parser.parse_args()
    print('Training configs: {}'.format(args))
    return args

if __name__ == "__main__":
    
    args = parser('config.yaml')
    env = get_env(args.env)()
    env_args = env.get_args()
    for k,v in env_args.items():
        if k == 'act':
            v = v & args.act
        setattr(args,k,v)
    
    dG = DataGenerator(env,seq_len=args.seq_len)
    events = generate_file(env.config['swmm_input'],env.config['rainfall'])
    if args.simulate:
        dG.generate(events,processes=args.processes,act=args.act,recurrent=args.recurrent)
        dG.save(args.data_dir)
    else:
        dG.load(args.data_dir)

    train_events = random.sample(range(len(events)),int(len(events)*args.ratio))
    test_events = [ev for ev in range(len(events)) if ev not in train_events]
    
    emul = Emulator(args.conv,args.edges,args.resnet,args.recurrent,args)
    emul.update_net(dG,train_events,args.epochs,args.batch_size)

    emul.evaluate_net(dG,test_events)

    for event_id in test_events:
        event = events[event_id]
        states,settings = dG.simulate(event,act=args.act)
        r = states[0:,...,-1]
        pred_states = emul.simulate(states[0],r)