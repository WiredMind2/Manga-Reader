from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.core.database import get_db
from app.core.schemas import UserPreferenceResponse, UserPreferenceUpdate
from app.models import User, UserPreference
from app.api.auth import get_current_user

router = APIRouter()


@router.get("/", response_model=UserPreferenceResponse)
async def get_user_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's preferences"""
    result = await db.execute(
        select(UserPreference).where(UserPreference.user_id == current_user.id)
    )
    preferences = result.scalar_one_or_none()
    
    if not preferences:
        # Create default preferences if they don't exist
        preferences = UserPreference(
            user_id=current_user.id,
            default_reading_direction="rtl",
            auto_next_chapter=True,
            page_fit_mode="fit-width",
            theme="dark",
            items_per_page=20,
            ocr_enabled=False,
            ocr_auto_translate=False,
            ocr_source_language="Japanese",
            ocr_target_language="English"
        )
        db.add(preferences)
        await db.commit()
        await db.refresh(preferences)
    
    return UserPreferenceResponse(
        id=preferences.id,
        user_id=preferences.user_id,
        default_reading_direction=preferences.default_reading_direction,
        auto_next_chapter=preferences.auto_next_chapter,
        page_fit_mode=preferences.page_fit_mode,
        theme=preferences.theme,
        items_per_page=preferences.items_per_page,
        ocr_enabled=preferences.ocr_enabled,
        ocr_auto_translate=preferences.ocr_auto_translate,
        ocr_source_language=preferences.ocr_source_language,
        ocr_target_language=preferences.ocr_target_language
    )


@router.put("/", response_model=UserPreferenceResponse)
async def update_user_preferences(
    preferences_update: UserPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user's preferences"""
    result = await db.execute(
        select(UserPreference).where(UserPreference.user_id == current_user.id).limit(1)
    )
    preferences = result.scalar_one_or_none()
    
    if not preferences:
        # Create new preferences if they don't exist
        preferences = UserPreference(
            user_id=current_user.id,
            default_reading_direction=preferences_update.default_reading_direction or "rtl",
            auto_next_chapter=preferences_update.auto_next_chapter if preferences_update.auto_next_chapter is not None else True,
            page_fit_mode=preferences_update.page_fit_mode or "fit-width",
            theme=preferences_update.theme or "dark",
            items_per_page=preferences_update.items_per_page or 20,
            ocr_enabled=preferences_update.ocr_enabled if preferences_update.ocr_enabled is not None else False,
            ocr_auto_translate=preferences_update.ocr_auto_translate if preferences_update.ocr_auto_translate is not None else False,
            ocr_source_language=preferences_update.ocr_source_language or "Japanese",
            ocr_target_language=preferences_update.ocr_target_language or "English"
        )
        db.add(preferences)
    else:
        # Update existing preferences
        update_data = preferences_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(preferences, field, value)
        
        # Mark the session as dirty to ensure the update is persisted
        db.add(preferences)
    
    await db.commit()
    await db.refresh(preferences)
    
    return UserPreferenceResponse(
        id=preferences.id,
        user_id=preferences.user_id,
        default_reading_direction=preferences.default_reading_direction,
        auto_next_chapter=preferences.auto_next_chapter,
        page_fit_mode=preferences.page_fit_mode,
        theme=preferences.theme,
        items_per_page=preferences.items_per_page,
        ocr_enabled=preferences.ocr_enabled,
        ocr_auto_translate=preferences.ocr_auto_translate,
        ocr_source_language=preferences.ocr_source_language,
        ocr_target_language=preferences.ocr_target_language
    )


@router.delete("/")
async def reset_user_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Reset user preferences to defaults"""
    result = await db.execute(
        select(UserPreference).where(UserPreference.user_id == current_user.id).limit(1)
    )
    preferences = result.scalar_one_or_none()
    
    if preferences:
        # Reset to defaults
        preferences.default_reading_direction = "rtl"
        preferences.auto_next_chapter = True
        preferences.page_fit_mode = "fit-width"
        preferences.theme = "dark"
        preferences.items_per_page = 20
        preferences.ocr_enabled = False
        preferences.ocr_auto_translate = False
        preferences.ocr_source_language = "Japanese"
        preferences.ocr_target_language = "English"
        
        await db.commit()
        await db.refresh(preferences)
        
        return UserPreferenceResponse(
            id=preferences.id,
            user_id=preferences.user_id,
            default_reading_direction=preferences.default_reading_direction,
            auto_next_chapter=preferences.auto_next_chapter,
            page_fit_mode=preferences.page_fit_mode,
            theme=preferences.theme,
            items_per_page=preferences.items_per_page,
            ocr_enabled=preferences.ocr_enabled,
            ocr_auto_translate=preferences.ocr_auto_translate,
            ocr_source_language=preferences.ocr_source_language,
            ocr_target_language=preferences.ocr_target_language
        )
    
    return {"message": "No preferences found to reset"}