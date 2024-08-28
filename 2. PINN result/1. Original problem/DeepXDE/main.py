import deepxde as dde  # A complete problem: data+PDE+FCNN+optimiser
import numpy as np
import pandas as pd
import wandb

import matplotlib.pyplot as plt
from matplotlib import cm

# wandb.log({"BC loss": BC_loss, "PDE loss": PDE_loss, "Total loss": total_loss})
# wandb.log({ 'Loss' : wandb.Image(fig2) })
def train():
    with wandb.init():
        config = wandb.config
        # Load the CSV files into DataFrames
        df_ground_truth = pd.read_csv('ground_truth.csv')
        df_pipeface_temp = pd.read_csv('PipeFace_Temperature.csv')
        df_tiletop_temp = pd.read_csv('TileTop_Temperature.csv')

        # Convert the DataFrames to NumPy arrays
        nodes = df_ground_truth.iloc[:, 0:3].to_numpy()
        nodal_coordinates_pipeface = df_pipeface_temp.iloc[:, 0:3].to_numpy()
        nodal_coordinates_tiletop = df_tiletop_temp.iloc[:, 0:3].to_numpy()

        # Vertically stack the nodal coordinates from both files
        #boundary_nodal_coordinates = np.vstack((nodal_coordinates_pipeface, nodal_coordinates_tiletop))

        # Extract the fourth column (the solution) from each DataFrame
        solution_pipeface = df_pipeface_temp.iloc[:, 3].to_numpy().reshape(-1, 1)
        solution_tiletop = df_tiletop_temp.iloc[:, 3].to_numpy().reshape(-1, 1)

        # Vertically stack the solutions from both files
        #boundary_solution = np.vstack((solution_pipeface.reshape(-1, 1), solution_tiletop.reshape(-1, 1)))


        #print(np.shape(nodes))
        #print(np.shape(boundary_nodal_coordinates), np.shape(boundary_solution))

        hard_constraint = False # set constraint type
        weights = 100  # if hard_constraint == False

        epochs = config.epochs
        # learning rate, the number of dense layers and nodes, and the activation function
        parameters = [config.lr, 8, 60, config.activation]

        learning_rate, num_dense_layers, num_dense_nodes, activation = parameters

        def pde(X,u):
            dy_xx = dde.grad.hessian(u, X, i=0, j=0)
            dy_yy = dde.grad.hessian(u, X, i=1, j=1)
            dy_zz = dde.grad.hessian(u, X, i=2, j=2)
            return dy_xx + dy_yy + dy_zz
            
        geom = dde.geometry.Cuboid(xmin=[-0.5,-0.5,0], xmax=[0.5,0.5,1]) # dummy geometry, not used at all

        observe_u_pipe = dde.icbc.PointSetBC(nodal_coordinates_pipeface, solution_pipeface) # all BCs and their solutions
        observe_u_top = dde.icbc.PointSetBC(nodal_coordinates_tiletop, solution_tiletop)

        data = dde.data.PDE(
            geom, # dummy geom
            pde,
            [observe_u_pipe, observe_u_top], # manual BC points
            num_domain = 0, # Anchor are used instead
            num_boundary = 0, # use bc points manually
            anchors=nodes
        )

        net = dde.nn.FNN(
            [3] + [num_dense_nodes] * num_dense_layers + [1],
            activation,
            "Glorot uniform"
        )

        model = dde.Model(data, net)
        loss_weights = [1,1,1] # lossweights [pde,BC]

        model.compile("adam",
                    lr=config.lr,
                    loss_weights=loss_weights)
                    
        # https://github.com/lululxvi/deepxde/discussions/1086#discussion-4657568
        class LossConvergence(dde.callbacks.Callback):
            def __init__(self):
                super().__init__()

            def on_epoch_begin(self):
                #print('Training loss : ',sum(self.model.train_state.loss_train))
                if sum(model.train_state.loss_train) < 1e-5: # convergence of training loss
                    print('Loss converged')
                    self.model.stop_training = True # stop the training
        # for wandb
        class CustomCallback(dde.callbacks.Callback):
            def __init__(self):
                super().__init__()
            
            def on_epoch_end(self):
                # Access and print the current epoch number.
                epoch = self.model.train_state.epoch
                # Log individual loss components.
                pde_loss = self.model.train_state.loss_train[0]
                pipe_loss = self.model.train_state.loss_train[1]
                top_tile_loss = self.model.train_state.loss_train[2]
                
                # Calculate and log the total loss.
                total_loss = sum(self.model.train_state.loss_train)
                
                # Use wandb.log to log the metrics for the current epoch
                wandb.log({"epoch": epoch,
                        "PDE loss": pde_loss,
                        "Pipe loss": pipe_loss,
                        "Top tile loss": top_tile_loss,
                        "Total loss": total_loss})

        # Then use this callback in your training
        wandb_callback = CustomCallback()

        loss_early_stop = LossConvergence()

        losshistory, train_state = model.train(epochs=epochs, display_every=100,callbacks=[loss_early_stop, wandb_callback])

        model.save('model',protocol='backend', verbose=0)

        dde.saveplot(losshistory, train_state, issave=True, isplot=True)

        print('Finished Training')

if __name__ == "__main__":
    train()










            


