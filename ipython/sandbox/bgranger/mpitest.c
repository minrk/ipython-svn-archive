#include <stdio.h>
#include <stdlib.h>
#include "mpi.h"

int main(int argc, char** argv){
  int rank;
  int i;

  for(i = 0; i< argc; i++){
    printf("arg %d = %s\n", i, argv[i]);
  }

  MPI_Init(&argc, &argv);
  MPI_Comm_rank(MPI_COMM_WORLD, &rank);
  printf("Hello from rank %d\n", rank);

  for(i = 0; i< argc; i++){
    printf("rank = %d, arg %d = %s\n", rank, i, argv[i]);
  }

  MPI_Finalize();
}

