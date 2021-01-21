import logging


logger = logging.getLogger('extract')


def extract(to_dict, from_dict):
    for key in to_dict.keys():
        extracted_val = from_dict.get(key)
        logger.debug('Getting {}.'.format(key))
        if extracted_val:
            logger.debug('Extracted from config {} = {}.'.format(key, extracted_val))
            to_dict[key] = extracted_val
