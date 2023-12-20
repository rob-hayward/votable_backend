# views.py
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from .serializers import VotableSerializer, VotableCreateSerializer
from .models import Vote, Votable
from rest_framework.decorators import api_view, permission_classes
from django.http import Http404


class GetSingleVotableView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, votable_id):
        try:
            votable = Votable.objects.get(id=votable_id)
        except Votable.DoesNotExist:
            raise Http404("Votable not found")

        serialized_data = VotableSerializer(votable, context={'request': request}).data
        return Response(serialized_data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_current_user(request):
    user_data = {
        "id": request.user.id,
        "username": request.user.username,
    }
    return Response(user_data)


class VoteView(APIView):
    def post(self, request, votable_id):
        user = request.user
        vote_value = request.data.get('vote')

        try:
            vote = Vote.objects.get(votable_id=votable_id, user=user)
            vote.vote = vote_value
            vote.save()
        except Vote.DoesNotExist:
            vote = Vote.objects.create(user=user, votable_id=votable_id, vote=vote_value)

        votable = Votable.objects.get(id=votable_id)
        votable.get_vote_data()  # Update vote data

        serialized_votable = VotableSerializer(votable, context={'request': request}).data
        return Response({'message': 'Vote recorded', 'votable': serialized_votable}, status=status.HTTP_200_OK)


class GetAllVotablesView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Fetching the 'order_by' query parameter. Default is 'created_at' if not provided.
        order_by = request.query_params.get('order_by', 'created_at')

        if order_by == 'created_at':
            votables = Votable.get_all_votables()
        elif order_by == 'votes':
            votables = Votable.get_votables_by_votes()
        elif order_by == 'consensus':
            votables = Votable.get_votables_by_consensus()
        elif order_by == 'popularity':
            votables = Votable.get_votables_by_popularity()
        else:
            return Response({'error': 'Invalid order_by parameter'}, status=status.HTTP_400_BAD_REQUEST)

        serialized_data = VotableSerializer(votables, many=True, context={'request': request}).data
        return Response(serialized_data, status=status.HTTP_200_OK)


class CreateVotableView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = VotableCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(creator=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)