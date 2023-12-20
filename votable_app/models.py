# models.py
from django.db import models
from django.contrib.auth.models import User
from enum import Enum
from django.db.models import Count
from math import sqrt
from django.db.models.functions import Greatest


class VoteType(Enum):
    POSITIVE = 1
    NEGATIVE = -1
    NO_VOTE = 0

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]

    @classmethod
    def default(cls):
        return cls.NO_VOTE.value


class VotableType(Enum):
    QUESTION = "Question"
    STATEMENT = "Statement"
    PROPOSAL = "Proposal"

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]


class Votable(models.Model):
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200, help_text="Short title to describe the votable content.")
    text = models.TextField()
    votable_type = models.CharField(max_length=20, choices=VotableType.choices())
    total_votes = models.PositiveIntegerField(default=0)
    positive_votes = models.PositiveIntegerField(default=0)
    negative_votes = models.PositiveIntegerField(default=0)
    participation_percentage = models.DecimalField(max_digits=3, decimal_places=0, default=0)
    positive_percentage = models.DecimalField(max_digits=3, decimal_places=0, default=0)
    negative_percentage = models.DecimalField(max_digits=3, decimal_places=0, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    wilson_score = models.DecimalField(max_digits=10, decimal_places=8, default=0.0)

    def get_vote_data(self):
        vote_data = Vote.objects.filter(votable=self).aggregate(
            positive_votes=Count('id', filter=models.Q(vote=VoteType.POSITIVE.value)),
            negative_votes=Count('id', filter=models.Q(vote=VoteType.NEGATIVE.value)),
        )
        positive_votes = vote_data['positive_votes']
        negative_votes = vote_data['negative_votes']
        total_votes = positive_votes + negative_votes
        total_users = User.objects.count()
        z = 1.96  # For 95% confidence
        phat = positive_votes / total_votes if total_votes > 0 else 0
        wilson_nominator = phat + (z ** 2) / (2 * total_votes) - z * sqrt(
            (phat * (1 - phat) + (z ** 2) / (4 * total_votes)) / total_votes)
        wilson_denominator = 1 + (z ** 2) / total_votes

        self.participation_percentage = round((total_votes / total_users) * 100) if total_users > 0 else 0
        self.positive_percentage = round((positive_votes / total_votes) * 100) if total_votes > 0 else 0
        self.negative_percentage = round((negative_votes / total_votes) * 100) if total_votes > 0 else 0
        self.total_votes = total_votes
        self.positive_votes = positive_votes
        self.negative_votes = negative_votes
        self.wilson_score = wilson_nominator / wilson_denominator

        self.save()

        vote_data = {
            'total_votes': total_votes,
            'positive_percentage': self.positive_percentage,
            'negative_percentage': self.negative_percentage,
            'participation_percentage': self.participation_percentage,
            'positive_votes': positive_votes,
            'negative_votes': negative_votes,
        }

        return vote_data

    def get_votes(self):
        return Vote.objects.filter(votable=self)

    def get_user_vote(self, user):
        try:
            vote = Vote.objects.get(votable=self, user=user)
            if vote.vote == VoteType.POSITIVE.value:
                return 'Positive'
            elif vote.vote == VoteType.NEGATIVE.value:
                return 'Negative'
            else:
                return 'No Vote'
        except Vote.DoesNotExist:
            return 'No Vote'

    @staticmethod
    def get_all_votables():
        return Votable.objects.all().order_by('-created_at')

    @staticmethod
    def get_votables_by_votes():
        return Votable.objects.all().order_by('-total_votes')

    @staticmethod
    def get_votables_by_consensus():
        # Use the `Greatest` function to determine the highest percentage
        votables = Votable.objects.annotate(
            percentage_agreement=Greatest('positive_percentage', 'negative_percentage')
        )
        # Order by percentage of agreement and then total votes
        return votables.order_by('-percentage_agreement', '-total_votes')

    @staticmethod
    def get_votables_by_popularity():
        return Votable.objects.all().order_by('-wilson_score')


class Vote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    votable = models.ForeignKey(Votable, on_delete=models.CASCADE)
    vote = models.IntegerField(choices=VoteType.choices(), default=VoteType.default())
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'votable']

