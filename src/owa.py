#! /usr/bin/python3


def owa_weights_values(number_of_values, beta):
    """Calculates the OWA weights with the original Yager formula
     More specifically, the function returns the weight w_i for the i-th smallest value.

    Parameters:
         number_of_values

    Returns:
         Weights for values [1, ... ,]. The first element (weights[0] is the largest weight)
    """
    weights = [0]*(number_of_values+1)
    rescale = 10000
    weights[1] = rescale*beta**(number_of_values-1) / \
        (1+beta)**(number_of_values-1)
    weights[2:] = [rescale*beta**(number_of_values-x)/(1+beta) **
                   (number_of_values+1-x) for x in range(2, number_of_values+1)]
    weights[0] = max(weights[1:])+1

    # print(["%0.5f" % x for x in weights[1:]])
    return weights


def owa_weights_distribution(max_rank):
    """Calculates the OWA weights with the distribution approach
    More specifically, the function returns the product of w_h and \bar{f}_h
    used in the last equation of page 54 of the article.
    With respect to the function above the function includes the calculation of beta and the values \bar{f}_h.
    These are application specific and must be reconsidered in a different application

    Parameters:
         max_rank: max rank expressed by the students

    Returns:
         Weights for rank values [0, 1, ... ,\Delta]. The first element (weights[0] is the largest value in weights)
    """
    number_of_values = max_rank  # the default, not used for numerical reasons and because in our instances it is never necessary to have m>8
    number_of_values = 8  # max number for which to use Yager formula, hardcoded to 8
    # preparing weights element 0 will become the m-th element
    weights = [0]*(number_of_values+1)
    # beta: smaller than the smallest perceived difference among values which is 1 and 1/Delta after normalization
    beta = 1.0/max_rank - 0.001
    # beta=1-0.001 # without normalization
    # f_i = [1]*(number_of_values+1)  # used in most of the calculations
    f_i = [x*1./number_of_values for x in range(number_of_values+1)] # described in the paper
    rescale = 10000
    weights[1] = rescale * f_i[1] * \
        beta**(number_of_values-1)/(1+beta)**(number_of_values-1)  # 1
    weights[2:] = [rescale * f_i[x] * beta**(number_of_values-x)/(1+beta)**(
        number_of_values+1-x) for x in range(2, number_of_values+1)]  # 2,3,...,number_of_values
    weights[0] = max(weights[1:])+1
    
    if max_rank > number_of_values:
        for _ in range(number_of_values, max_rank):    
            weights.append(weights[0])

    # print(["%0.5f" % x for x in weights[1:]])
    return weights



owa_weights = owa_weights_distribution


if __name__ == "__main__":
    import functools

    # Example from Yager 1997b p 185:
    number_of_values = 4
    f_i_x = [1, 0.8, 0.7, 0.6]
    f_i_y = [1, 0.9, 0.8, 0.6]
    f_i_z = [1, 0.9, 0.7, 0.4]
    beta = 0.01  # delta in the paper: smaller than the smallest difference which is 0.1

    weights = [0]*(number_of_values+1)
    weights[1] = beta**(number_of_values-1)/(1+beta)**(number_of_values-1)
    weights[2:] = map(lambda x: beta**(number_of_values-x)/(1+beta)
                      ** (number_of_values+1-x), range(2, number_of_values+1))
    print(weights)

    # check: should give the same as previous line
    print(owa_weights_values(4, beta)[1:])

    print(sum(f_i_x[i-1]*weights[i] for i in range(1, number_of_values+1)))
    print(sum(f_i_y[i-1]*weights[i] for i in range(1, number_of_values+1)))
    print(sum(f_i_z[i-1]*weights[i] for i in range(1, number_of_values+1)))

    print("#####################################################################")
    # Original Yager's OWA and example in the article
    weights = owa_weights_values(10, beta=(1.0/8-0.001))
    print(weights[1:])

    v_1 = [1, 2, 2, 3, 4, 5, 5, 6, 7, 8]
    v_2 = [1, 2, 2, 3, 4, 4, 5, 6, 7, 8]

    fbar_i_1 = [v_1[i]/8 for i in range(10)]  # since already ordered
    fbar_i_2 = [v_2[i]/8 for i in range(10)]  # since already ordered

    sv_1 = sum([weights[i+1]*fbar_i_1[i] for i in range(1, 10)])
    sv_2 = sum([weights[i+1]*fbar_i_2[i] for i in range(1, 10)])

    print(sv_1)
    print(sv_2)

    print("#####################################################################")
    # used in the article:
    weights = owa_weights_distribution(8)
    print(weights[1:])
    weights = owa_weights_distribution(10)
    print(weights[1:])
