import random

import constants


def initialize_chromosomes(num_chromosomes, UEs, FCNs):
    """
    Initialize a population of chromosomes.
    Each chromosome represents the allocation of UEs to a specific FCN.

    :param num_chromosomes: Number of chromosomes in the population.
    :param UEs: List of UEs.
    :param FCNs: List of FCNs.
    :return: A list of chromosomes.
    """
    population = []
    for _ in range(num_chromosomes):
        chromosome = []
        for ue in UEs:
            fcn = random.choice(FCNs)
            gene = (ue.pk, fcn.pk, ue.Data_Size_Du, ue.Computation_Resource_fu)
            chromosome.append(gene)
        population.append(chromosome)
    return population


def calculate_fitness(ue_list, fcn, λEu, λTu):
    """
    Calculate the fitness (revenue) for a given FCN and its allocated UEs.

    :param ue_list: List of UEs allocated to this FCN.
    :param fcn: The FCN for which fitness is being calculated.
    :param λEu: Weight for energy consumption.
    :param λTu: Weight for latency.
    :return: The calculated fitness value.
    """
    total_revenue = 0
    total_computation_resource = sum(ue.Computation_Resource_fu for ue in ue_list)

    if total_computation_resource > fcn.cF:
        # If the total required computation resources exceed the FCN's capacity,
        # this allocation is not feasible.
        return float('-inf')

    for ue in ue_list:

        for i in range(constants.F):
            if fcn.pk == i + 1:
                r_uf = ue.get_Uplink_Rate_ruf(i + 1)  # Uplink rate for this UE to this FCN
                tau_uf = ue.get_Average_Sojourn_Time_tauuf(i + 1)  # Sojourn time for this UE to this FCN

                E_tu = ue.Transmission_Power_Pu * (ue.Data_Size_Du / r_uf)  # Transmission energy
                T_tu = ue.Data_Size_Du / r_uf + tau_uf  # Transmission time + sojourn time

                Q_tu = λEu * E_tu + λTu * T_tu  # Quality of service metric
                total_revenue += Q_tu  # Accumulate the revenue

    return total_revenue


def select_parents(population, fitness_values):
    """Select two parent chromosomes based on fitness values."""
    selected_indices = sorted(range(len(population)), key=lambda i: fitness_values[i], reverse=True)[:2]
    return population[selected_indices[0]], population[selected_indices[1]]


def crossover(parent1, parent2):
    """Perform crossover between two parent chromosomes."""
    crossover_point = random.randint(1, len(parent1) - 2)
    offspring1 = parent1[:crossover_point] + parent2[crossover_point:]
    offspring2 = parent2[:crossover_point] + parent1[crossover_point:]
    return offspring1, offspring2


def mutate(chromosome, num_fcns):
    """Mutate a chromosome by randomly changing one of its genes."""
    mutation_point = random.randint(0, len(chromosome) - 1)
    new_fcn = random.randint(1, num_fcns)
    gene = list(chromosome[mutation_point])
    gene[1] = new_fcn
    chromosome[mutation_point] = tuple(gene)
    return chromosome


def roga_algorithm(UEs, FCNs, num_generations, crossover_rate, mutation_rate):
    num_chromosomes = 4
    population = initialize_chromosomes(num_chromosomes, UEs, FCNs)

    print("Initial Population:")
    for chromosome in population:
        print(chromosome)
    # Run the genetic algorithm
    for generation in range(num_generations):
        # Evaluate fitness
        fitness_values = []
        for chromosome in population:
            fitness = 0
            for fcn in FCNs:
                ue_indices = [i for i, gene in enumerate(chromosome) if gene[1] == fcn.pk]
                ue_list = [UEs[i] for i in ue_indices]
                fitness += calculate_fitness(ue_list, fcn, constants.λEu, constants.λTu)
            fitness_values.append(fitness)

        # Selection
        parent1, parent2 = select_parents(population, fitness_values)

        # Crossover
        if random.random() < crossover_rate:
            offspring1, offspring2 = crossover(parent1, parent2)
        else:
            offspring1, offspring2 = parent1, parent2

        # Mutation
        if random.random() < mutation_rate:
            offspring1 = mutate(offspring1, len(FCNs))
        if random.random() < mutation_rate:
            offspring2 = mutate(offspring2, len(FCNs))

        # Replace the population with offspring
        population = [parent1, parent2, offspring1, offspring2]

        print(f"Generation {generation + 1}: Fitness Values = {fitness_values}")
    # Final population
    print("Final Population:")
    for chromosome in population:
        print(chromosome)
