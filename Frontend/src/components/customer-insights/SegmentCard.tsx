/**
 * Segment Card Component
 * Displays information about an audience segment
 */

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '../ui/collapsible';
import { Users, AlertCircle, Heart, ChevronDown, ChevronUp } from 'lucide-react';

interface SegmentCardProps {
  segment: {
    segment_id: string;
    segment_name: string;
    summary: string;
    pain_points: string[];
    interests: string[];
    discussion_count: number;
  };
}

export default function SegmentCard({ segment }: SegmentCardProps) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <Card className="glass border-border/50">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-xl flex items-center gap-2">
              <Users className="h-5 w-5 text-primary" />
              {segment.segment_name}
            </CardTitle>
            <CardDescription className="mt-2">
              {segment.summary}
            </CardDescription>
          </div>
          <Badge variant="secondary">
            {segment.discussion_count} discussions
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <Collapsible open={isOpen} onOpenChange={setIsOpen}>
          <div className="space-y-4">
            {/* Pain Points Preview */}
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm font-medium">
                <AlertCircle className="h-4 w-4 text-destructive" />
                <span>Pain Points</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {segment.pain_points.slice(0, 3).map((point, index) => (
                  <Badge key={index} variant="outline" className="text-xs">
                    {point}
                  </Badge>
                ))}
                {segment.pain_points.length > 3 && (
                  <Badge variant="outline" className="text-xs">
                    +{segment.pain_points.length - 3} more
                  </Badge>
                )}
              </div>
            </div>

            {/* Interests Preview */}
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm font-medium">
                <Heart className="h-4 w-4 text-primary" />
                <span>Interests</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {segment.interests.slice(0, 3).map((interest, index) => (
                  <Badge key={index} variant="secondary" className="text-xs">
                    {interest}
                  </Badge>
                ))}
                {segment.interests.length > 3 && (
                  <Badge variant="secondary" className="text-xs">
                    +{segment.interests.length - 3} more
                  </Badge>
                )}
              </div>
            </div>

            {/* Expandable Details */}
            <CollapsibleContent className="space-y-4">
              {segment.pain_points.length > 3 && (
                <div className="space-y-2 pt-2 border-t">
                  <p className="text-sm font-medium">All Pain Points:</p>
                  <div className="flex flex-wrap gap-2">
                    {segment.pain_points.map((point, index) => (
                      <Badge key={index} variant="outline" className="text-xs">
                        {point}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              {segment.interests.length > 3 && (
                <div className="space-y-2 pt-2 border-t">
                  <p className="text-sm font-medium">All Interests:</p>
                  <div className="flex flex-wrap gap-2">
                    {segment.interests.map((interest, index) => (
                      <Badge key={index} variant="secondary" className="text-xs">
                        {interest}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </CollapsibleContent>

            {/* Toggle Button */}
            {(segment.pain_points.length > 3 || segment.interests.length > 3) && (
              <CollapsibleTrigger asChild>
                <Button variant="ghost" size="sm" className="w-full">
                  {isOpen ? (
                    <>
                      <ChevronUp className="mr-2 h-4 w-4" />
                      Show Less
                    </>
                  ) : (
                    <>
                      <ChevronDown className="mr-2 h-4 w-4" />
                      Show More
                    </>
                  )}
                </Button>
              </CollapsibleTrigger>
            )}
          </div>
        </Collapsible>
      </CardContent>
    </Card>
  );
}
