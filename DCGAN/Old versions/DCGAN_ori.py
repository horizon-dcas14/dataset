# -*- coding: utf-8 -*-
"""
Created on Tue May 28 16:16:14 2019

@author: ftxsilva
"""

#%% Importing modules
from __future__ import print_function
#%matplotlib inline
import argparse
import csv
import os
import random
import torch
import torch.nn as nn
import torch.nn.parallel
import torch.backends.cudnn as cudnn
import torch.optim as optim
import torch.utils.data
from torch.utils.data import Dataset, DataLoader
import torchvision.datasets as dset
import torchvision.transforms as transforms
import torchvision.utils as vutils
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from IPython.display import HTML
import time

#%% Initializing parameters
# Set random seem for reproducibility
manualSeed = 999
#manualSeed = random.randint(1, 10000) # use if you want new results
print("Random Seed: ", manualSeed)
random.seed(manualSeed)
torch.manual_seed(manualSeed)

# Root directory for dataset
dataroot = "../Data/Autonomous data/"
# Number of workers for dataloader
workers = 0
# Batch size during training
batch_size = 150
# Number of channels in the training data.
nc = 1
# Size of z latent vector (i.e. size of generator input)
nz = 100
# Size of feature maps in generator
ngf = 30
# Size of feature maps in discriminator
ndf = 30
# Number of training epochs
num_epochs = 20
# Learning rate for optimizers
lr = 0.0002
# Beta1 hyperparam for Adam optimizers
beta1 = 0.5
# Number of GPUs available. Use 0 for CPU mode.
ngpu = 0


"""
Create the appropriate dataset class format for our problem

"""
#%% Dataset creation
def get_data(dataroot):
    
    df = pd.read_csv(dataroot, usecols = ['robot_x', 'robot_y', 'robot_theta'])
   
    df = df.values
   
    df = torch.DoubleTensor([df])
    df.float()
  
    return df #.values

data_sets = dset.DatasetFolder(dataroot, 
                                   loader=get_data, extensions = ['.csv'])
dataloader = torch.utils.data.DataLoader(data_sets, batch_size, shuffle = True, num_workers = workers)
# Decide which device we want to run on
device = torch.device("cuda:0" if (torch.cuda.is_available() and ngpu > 0) else "cpu")

#%% weights initialization
# further used in the generator and discriminator
def weights_init(m):
    classname = m.__class__.__name__
    if classname.find('Conv') != -1:
        nn.init.normal_(m.weight.data, 0.0, 0.02)
        m.weight.data = m.weight.data.float()
    elif classname.find('BatchNorm') != -1:
        nn.init.normal_(m.weight.data, 1.0, 0.02)
        nn.init.constant_(m.bias.data, 0)
        m.weight.data = m.weight.data.float()
        m.bias.data = m.bias.data.float()
        

#%% Create the generator
# Generator Code
class Generator(nn.Module):
    def __init__(self, ngpu):
        super(Generator, self).__init__()
        self.ngpu = ngpu
        self.main = nn.Sequential(
            # input is Z, going into a convolution
            nn.ConvTranspose2d( nz, ngf * 8, (2,1), 1, 0, bias=False),
            nn.BatchNorm2d(ngf * 8),
            nn.ReLU(True),
            # state size. (ngf*8) x 2 x 1
            nn.ConvTranspose2d(ngf * 8, ngf * 4, (3,1), 1, 0, bias=False),
            nn.BatchNorm2d(ngf * 4),
            nn.ReLU(True),
            # state size. (ngf*4) x 4 x 1
            nn.ConvTranspose2d(ngf * 4, ngf * 2, (3,1), 1, 0, bias=False),
            nn.BatchNorm2d(ngf * 2),
            nn.ReLU(True),
            # state size. (ngf*2) x 6 x 1
            nn.ConvTranspose2d(ngf * 2, ngf*1, (3,1), 1, 0, bias=False),
            nn.BatchNorm2d(ngf*1),
            nn.ReLU(True),
            # state size. (ngf) x 8 x 1
            nn.ConvTranspose2d( ngf, 1, (3,3), 1, 0, bias=False),
            nn.Tanh()
            # state size. (1) x 10 x 24
        )
    def forward(self, input):
            return self.main(input)
        
# Create the generator
netG = Generator(ngpu).to(device)
netG = netG.float()
# Handle multi-gpu if desired
if (device.type == 'cuda') and (ngpu > 1):
    netG = nn.DataParallel(netG, list(range(ngpu)))
# Apply the weights_init function to randomly initialize all weights
#  to mean=0, stdev=0.2.
netG.apply(weights_init)

#%% Create the discriminator
# Discriminator architecture
class Discriminator(nn.Module):
    def __init__(self, ngpu):
        super(Discriminator, self).__init__()
        self.ngpu = ngpu
        self.main = nn.Sequential(
            # input is (nc=1) x 10 x 24
            nn.Conv2d(nc, ndf, (3,3), 1, 0, bias=False),
            nn.LeakyReLU(0.2, inplace=True),
            # state size. (ndf) x 8 x 1
            nn.Conv2d(ndf, ndf * 2, (3,1), 1, 0, bias=False),
            nn.BatchNorm2d(ndf * 2),
            nn.LeakyReLU(0.2, inplace=True),
            # state size. (ndf) x 6 x 1
            nn.Conv2d(ndf * 2, ndf * 4, (3,1), 1, 0, bias=False),
            nn.BatchNorm2d(ndf * 4),
            nn.LeakyReLU(0.2, inplace=True),
            # state size. (ndf) x 4 x 1
            nn.Conv2d(ndf * 4, ndf * 8, (3,1), 1, 0, bias=False),
            nn.BatchNorm2d(ndf * 8),
            nn.LeakyReLU(0.2, inplace=True),
            # state size. (ndf*2) x 2 x 1
            nn.Conv2d(ndf * 8, 1, (2,1), 1, 0, bias=False),
            nn.Sigmoid()
        )
    def forward(self, input):
            return self.main(input)
        
# Create the Discriminator
netD = Discriminator(ngpu).to(device)
netD = netD.float()
# Handle multi-gpu if desired
if (device.type == 'cuda') and (ngpu > 1):
    netD = nn.DataParallel(netD, list(range(ngpu)))
# Apply the weights_init function to randomly initialize all weights
#  to mean=0, stdev=0.2.
netD.apply(weights_init)


#%% Loss function and optimizer initialization
# Initialize BCELoss function
criterion = nn.BCELoss()

# Create batch of latent vectors that we will use to visualize
#  the progression of the generator
fixed_noise = torch.randn(64, nz, 1, 1, device=device)

# Establish convention for real and fake labels during training
real_label = 1
fake_label = 0

# Setup Adam optimizers for both G and D
optimizerD = optim.Adam(netD.parameters(), lr=lr, betas=(beta1, 0.999))
optimizerG = optim.Adam(netG.parameters(), lr=lr, betas=(beta1, 0.999))

#%% Training the DCGAN
# Training Loop

# Lists to keep track of progress
csv_list = []
G_losses = []
D_losses = []
iters = 0
netD = netD.float()
netG = netG.float()

print("Starting Training Loop...")
# For each epoch
for epoch in range(num_epochs):
    # For each batch in the dataloader
    print('Epoch : ', epoch)
    for i, data in enumerate(dataloader, 0):
        #for j in range(128):
        data[0] = data[0].float()
        # (1) Update D network: maximize log(D(x)) + log(1 - D(G(z)))
        ###########################
        ## Train with all-real batch
        netD.zero_grad()
        # Format batch
        real_cpu = data[0].to(device)
        b_size = real_cpu.size(0)
        label = torch.full((b_size,), real_label, device=device)
        # Forward pass real batch through D
        output = netD(real_cpu).view(-1)
        # Calculate loss on all-real batch
        errD_real = criterion(output, label)
        # Calculate gradients for D in backward pass
        errD_real.backward()
        D_x = output.mean().item()

        ## Train with all-fake batch
        # Generate batch of latent vectors
        noise = torch.randn(b_size, nz, 1, 1, device=device)
        # Generate fake image batch with G
        fake = netG(noise)
        label.fill_(fake_label)
        # Classify all fake batch with D
        output = netD(fake.detach()).view(-1)
        # Calculate D's loss on the all-fake batch
        errD_fake = criterion(output, label)
        # Calculate the gradients for this batch
        errD_fake.backward()
        D_G_z1 = output.mean().item()
        # Add the gradients from the all-real and all-fake batches
        errD = errD_real + errD_fake
        # Update D
        optimizerD.step()

        ############################
        # (2) Update G network: maximize log(D(G(z)))
        ###########################
        netG.zero_grad()
        label.fill_(real_label)  # fake labels are real for generator cost
        # Since we just updated D, perform another forward pass of all-fake batch through D
        output = netD(fake).view(-1)
        # Calculate G's loss based on this output
        errG = criterion(output, label)
        # Calculate gradients for G
        errG.backward()
        D_G_z2 = output.mean().item()
        # Update G
        optimizerG.step()

        # Output training stats
        if i % 50 == 0:
            print('[%d/%d][%d/%d]\tLoss_D: %.4f\tLoss_G: %.4f\tD(x): %.4f\tD(G(z)): %.4f / %.4f'
                  % (epoch, num_epochs, i, len(dataloader),
                     errD.item(), errG.item(), D_x, D_G_z1, D_G_z2))

        # Save Losses for plotting later
        G_losses.append(errG.item())
        D_losses.append(errD.item())

        # Check how the generator is doing by saving G's output on fixed_noise
        if (iters % 500 == 0) or ((epoch == num_epochs-1) and (i == len(dataloader)-1)):
            with torch.no_grad():
                fake = netG(fixed_noise).detach().cpu()
            csv_list.append(fake)

        iters += 1

for i in range(len(csv_list)):
    with open('Results/results_' + str(i) + '.csv', 'w', newline = '') as alldata :
        writer = csv.writer(alldata,delimiter=',')
        j=0;
        for j in range(len(csv_list[i])):
            writer.writerows(csv_list[i][j])
            j+=1
            
plt.figure(figsize=(10,5))
plt.title('Generator and Discriminator Loss During Training Lr = '+str(lr)+' beta1='+str(beta1))
plt.plot(G_losses,label="G")
plt.plot(D_losses,label="D")
plt.xlabel("iterations")
plt.ylabel("Loss")
plt.legend()
plt.savefig('losses_'+str(i)+'.png')
plt.show()