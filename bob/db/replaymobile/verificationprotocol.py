#!/usr/bin/env python
# vim: set fileencoding=utf-8 :

"""   The Replay-Mobile Database for face spoofing interface. It is an
extension of an SQL-based database interface, which directly talks to Replay-
Mobile database, for verification experiments (good to use in bob.bio.base
framework). It also implements a kind of hack so that you can run
vulnerability analysis with it. """

from bob.db.base import File as BaseFile
from bob.db.base import FileDatabase as BaseDatabase
from .query import Database as LDatabase


def selected_indices(total_number_of_indices, desired_number_of_indices=None):
    """
    Returns a list of indices that will contain exactly the number of desired
    indices (or the number of total items in the list, if this is smaller).
    These indices are selected such that they are evenly spread over the whole
    sequence.
    """

    if desired_number_of_indices is None or \
            desired_number_of_indices >= total_number_of_indices or \
            desired_number_of_indices < 0:
        return range(total_number_of_indices)
    increase = float(total_number_of_indices) / \
        float(desired_number_of_indices)
    # generate a regular quasi-random index list
    return [int((i + .5) * increase) for i in range(desired_number_of_indices)]


class File(BaseFile):
    """
    Replay Mobile low-level file used for vulnerability analysis in face
    recognition
    """

    def __init__(self, f, framen=None):
        self._f = f
        self.framen = framen
        self.original_path = f.path
        self.path = '{}_{:03d}'.format(f.path, framen)
        self.client_id = f.client_id
        self.file_id = '{}_{}'.format(f.id, framen)
        super(File, self).__init__(path=self.path, file_id=self.file_id)

    def load(self, directory=None, extension=None):
        if extension in (None, '.mov'):
            for i in range(100):
                try:
                    video = self._f.load(directory, extension)
                    # just return the required frame.
                    return video[self.framen]
                except RuntimeError:
                    pass
        else:
            return super(File, self).load(directory, extension)

    @property
    def annotations(self):
        return self._f.annotations[str(self.framen)]


class Database(BaseDatabase):
    """
    Implements verification API for querying Replay Mobile database.
    This database loads max_number_of_frames from the video files as
    separate samples. This is different from what bob.bio.video does
    currently.
    """
    __doc__ = __doc__

    def __init__(self,
                 max_number_of_frames=None,
                 original_directory=None,
                 original_extension=None,
                 annotation_directory=None,
                 annotation_extension='.json',
                 annotation_type='json',
                 ):

        # call base class constructors to open a session to the database
        self._db = LDatabase(
            original_directory=original_directory,
            original_extension=original_extension,
            annotation_directory=annotation_directory,
            annotation_extension=annotation_extension,
            annotation_type=annotation_type,
        )

        super(Database, self).__init__(original_directory, original_extension)

        self.max_number_of_frames = max_number_of_frames or 10
        # 240 is the guaranteed number of frames in replay mobile videos
        self.indices = selected_indices(240, self.max_number_of_frames)
        self.low_level_group_names = ('train', 'devel', 'test')
        self.high_level_group_names = ('world', 'dev', 'eval')

    @property
    def original_directory(self):
        return self._db.original_directory

    @original_directory.setter
    def original_directory(self, value):
        self._db.original_directory = value

    @property
    def original_extension(self):
        return self._db.original_extension

    @original_extension.setter
    def original_extension(self, value):
        self._db.original_extension = value

    @property
    def annotation_directory(self):
        return self._db.annotation_directory

    @annotation_directory.setter
    def annotation_directory(self, value):
        self._db.annotation_directory = value

    @property
    def annotation_extension(self):
        return self._db.annotation_extension

    @annotation_extension.setter
    def annotation_extension(self, value):
        self._db.annotation_extension = value

    @property
    def annotation_type(self):
        return self._db.annotation_type

    @annotation_type.setter
    def annotation_type(self, value):
        self._db.annotation_type = value

    def protocol_names(self):
        """Returns all registered protocol names
        Here I am going to hack and double the number of protocols
        with -licit and -spoof. This is done for running vulnerability
        analysis"""
        names = [p.name + '-licit' for p in self._db.protocols()]
        names += [p.name + '-spoof' for p in self._db.protocols()]
        return names

    def groups(self):
        return self.convert_names_to_highlevel(
            self._db.groups(), self.low_level_group_names,
            self.high_level_group_names)

    def model_ids_with_protocol(self, groups=None, protocol=None, **kwargs):
        # since the low-level API does not support verification
        # straight-forward-ly, we improvise.
        files = self.objects(groups=groups, protocol=protocol,
                             purposes='enroll', **kwargs)
        return sorted(set(f.client_id for f in files))

    def objects(self, groups=None, protocol=None, purposes=None,
                model_ids=None, **kwargs):
        if protocol == '.':
            protocol = None
        protocol = self.check_parameter_for_validity(
            protocol, "protocol", self.protocol_names(), 'grandtest-licit')
        groups = self.check_parameters_for_validity(
            groups, "group", self.groups(), self.groups())
        purposes = self.check_parameters_for_validity(
            purposes, "purpose", ('enroll', 'probe'), ('enroll', 'probe'))
        purposes = list(purposes)
        groups = self.convert_names_to_lowlevel(
            groups, self.low_level_group_names, self.high_level_group_names)

        # protocol licit is not defined in the low level API
        # so do a hack here.
        if '-licit' in protocol:
            # for licit we return the grandtest protocol
            protocol = protocol.replace('-licit', '')
            # The low-level API has only "attack", "real", "enroll" and "probe"
            # should translate to "real" or "attack" depending on the protocol.
            # enroll does not to change.
            if 'probe' in purposes:
                purposes.remove('probe')
                purposes.append('real')
                if len(purposes) == 1:
                    # making the model_ids to None will return all clients
                    # which make the impostor data also available.
                    model_ids = None
                elif model_ids:
                    raise NotImplementedError(
                        'Currently returning both enroll and probe for '
                        'specific client(s) in the licit protocol is not '
                        'supported. Please specify one purpose only.')

        elif '-spoof' in protocol:
            protocol = protocol.replace('-spoof', '')
            # you need to replace probe with attack and real for the spoof
            # protocols. You can add the real here also to create positives
            # scores also but usually you get these scores when you run the
            # licit protocol
            if 'probe' in purposes:
                purposes.remove('probe')
                purposes.append('attack')

        # now, query the actual Replay database
        objects = self._db.objects(
            groups=groups, protocol=protocol, cls=purposes, clients=model_ids,
            **kwargs)

        # make sure to return File representation of a file, not the database
        # one also make sure you replace client ids with attack
        retval = []
        for f in objects:
            for i in self.indices:
                if f.is_real():
                    retval.append(File(f, i))
                else:
                    temp = File(f, i)
                    attack = f.get_attack()
                    temp.client_id = 'attack/{}'.format(
                        attack.attack_device, attack.attack_support)
                    retval.append(temp)
        return retval
